import sys
import os
import time
import threading
import traceback
from datetime import datetime
import psutil

# --- Imports for PySide6 ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QFrame, QProgressBar, QScrollArea,
    QComboBox, QTreeWidget, QTreeWidgetItem, QTextEdit, QFileDialog, QMessageBox,
    QSizePolicy, QHeaderView, QSplitter, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot, QEasingCurve, QPropertyAnimation, QEvent
from PySide6.QtGui import QFont, QColor, QIcon

# --- Import icon library ---
import qtawesome as qta

# --- Import from our existing modules ---
# (Giả sử các file này tồn tại trong cùng thư mục)
import config
import file_operations
import drive_manager
from kafka_producer import KafkaManager

# --- Helper Function ---
def get_drive_name_from_mountpoint(mountpoint):
    """Lấy tên thư mục gọn gàng từ điểm gắn của ổ đĩa."""
    if not mountpoint:
        return "Unknown_Drive"
    if sys.platform == "win32" and ":" in mountpoint:
        return f"Drive {mountpoint.split(':')[0]}"
    name = os.path.basename(mountpoint)
    return name if name else "Unknown_Drive"

# --- Worker for background tasks (Không thay đổi logic) ---
class WorkerSignals(QObject):
    finished = Signal(object, str, list)
    progress = Signal(int, int, str)
    file_status = Signal(str, str, str, object, object)
    file_time = Signal(str, float)
    log = Signal(str, str)

class CopyWorker(QObject):
    """Xử lý quá trình sao chép trong một luồng riêng biệt."""
    def __init__(self, videos, destination_root, should_wipe, item_ids, process_id, conflict_policy):
        super().__init__()
        self.videos = videos
        self.destination_root = destination_root
        self.should_wipe = should_wipe
        self.item_ids = item_ids
        self.process_id = process_id
        self.conflict_policy = conflict_policy
        self.signals = WorkerSignals()
        self.is_running = True

    def run(self):
        try:
            final_results = {"success": 0, "error": 0, "skipped": 0}
            successfully_copied_paths = []
            total_files = len(self.videos)

            for i, video_info in enumerate(self.videos):
                if not self.is_running:
                    break

                start_time = time.time()
                source_path = video_info['path']
                file_name = os.path.basename(source_path)
                item_id = self.item_ids[i]

                self.signals.progress.emit(i + 1, total_files, file_name)

                drive_name = get_drive_name_from_mountpoint(self.process_id)
                final_destination_folder = os.path.join(self.destination_root, drive_name)
                try:
                    os.makedirs(final_destination_folder, exist_ok=True)
                except OSError as e:
                    self.signals.log.emit(f"Không thể tạo thư mục {final_destination_folder}: {e}", "ERROR")
                    final_results["error"] += 1
                    continue

                def status_callback(status_key, status_text, progress_value=None, speed_mbps=None):
                    self.signals.file_status.emit(item_id, status_text, status_key, progress_value, speed_mbps)
                    if "Sao chép (" not in status_text:
                        self.signals.log.emit(f"{file_name}: {status_text}", status_key.upper())

                try:
                    success, skipped, final_dest_path = file_operations.copy_and_verify_file(
                        source_path, final_destination_folder, self.conflict_policy, status_callback
                    )
                    if success:
                        final_results["success"] += 1
                        if skipped:
                            final_results["skipped"] += 1
                        else:
                            if final_dest_path:
                                successfully_copied_paths.append(final_dest_path)
                    else:
                        final_results["error"] += 1
                except Exception as e:
                    final_results["error"] += 1
                    status_callback("error", f"Lỗi nghiêm trọng: {e}", -1.0)

                duration = time.time() - start_time
                self.signals.file_time.emit(item_id, duration)

            if self.is_running:
                all_files_processed_successfully = final_results["error"] == 0
                drive_name_for_report = get_drive_name_from_mountpoint(self.process_id)

                if all_files_processed_successfully:
                    if self.should_wipe:
                        def wipe_status_callback(status_key, status_text, progress_value=None):
                            self.signals.log.emit(f"Xóa thẻ {drive_name_for_report}: {status_text}", status_key.upper())
                        
                        self.signals.log.emit(f"Bắt đầu xóa sạch thẻ {drive_name_for_report}...", "INFO")
                        wipe_success, wipe_message = file_operations.wipe_drive_data(self.process_id, wipe_status_callback)
                        self.signals.log.emit(f"Kết quả xóa thẻ {drive_name_for_report}: {wipe_message}", "SUCCESS" if wipe_success else "ERROR")
            
            self.signals.finished.emit(final_results, self.process_id, successfully_copied_paths)

        except Exception:
            tb_str = traceback.format_exc()
            self.signals.log.emit(f"Lỗi nghiêm trọng trong luồng sao chép: {tb_str}", "CRITICAL")
            self.signals.finished.emit({"success": 0, "error": len(self.videos), "skipped": 0}, self.process_id, [])

    def stop(self):
        self.is_running = False

class DriveMonitor(QObject):
    """Giám sát thay đổi ổ đĩa trong luồng nền."""
    drives_changed = Signal()
    log = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.monitoring = True

    def run(self):
        known_mountpoints = {p.mountpoint for p in drive_manager.get_removable_drives()}
        while self.monitoring:
            try:
                if sys.platform.startswith("linux"):
                    drive_manager.find_and_mount_unmounted_drives()
                current_mountpoints = {p.mountpoint for p in drive_manager.get_removable_drives()}
                if current_mountpoints != known_mountpoints:
                    self.drives_changed.emit()
                    known_mountpoints = current_mountpoints
            except Exception as e:
                self.log.emit(f"Lỗi trong luồng giám sát ổ đĩa: {e}", "ERROR")
            time.sleep(3)

    def stop(self):
        self.monitoring = False

# --- Custom Widgets (Phiên bản màu mè) ---
class DriveWidget(QWidget):
    """Widget thẻ hiển thị thông tin một ổ đĩa, được thiết kế lại hoàn toàn."""
    selection_changed = Signal(str, bool)

    def __init__(self, mountpoint, description, total_size_gb):
        super().__init__()
        self.mountpoint = mountpoint
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(0)

        self.container_frame = QFrame(self)
        self.container_frame.setObjectName("DriveWidgetFrame")
        
        frame_layout = QGridLayout(self.container_frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(8)
        frame_layout.setColumnStretch(2, 1)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.on_toggle)
        frame_layout.addWidget(self.checkbox, 0, 0, 2, 1, Qt.AlignmentFlag.AlignTop)

        drive_icon_label = QLabel()
        drive_icon_label.setPixmap(qta.icon('fa5s.hdd', color='#DCE1E8').pixmap(24, 24))
        frame_layout.addWidget(drive_icon_label, 0, 1, 2, 1, Qt.AlignmentFlag.AlignTop)

        self.name_label = QLabel(f"<b>{get_drive_name_from_mountpoint(mountpoint)}</b>")
        self.name_label.setObjectName("DriveNameLabel")
        frame_layout.addWidget(self.name_label, 0, 2)
        
        self.status_icon = QLabel()
        frame_layout.addWidget(self.status_icon, 0, 3, Qt.AlignmentFlag.AlignRight)

        self.speed_label = QLabel("")
        self.speed_label.setObjectName("DriveSpeedLabel")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        frame_layout.addWidget(self.speed_label, 0, 4)
        
        desc_text = f"{total_size_gb:.1f} GB | {description}"
        self.description_label = QLabel(desc_text)
        self.description_label.setObjectName("DriveDescLabel")
        frame_layout.addWidget(self.description_label, 1, 2, 1, 3)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("DriveProgressBar")
        
        main_layout.addWidget(self.container_frame)
        main_layout.addWidget(self.progress_bar)

    def on_toggle(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.selection_changed.emit(self.mountpoint, is_checked)
        self.container_frame.setProperty("checked", "true" if is_checked else "false")
        self.container_frame.style().polish(self.container_frame)

    def start_scan(self):
        self.progress_bar.setRange(0, 0)
        self.checkbox.setEnabled(False)
        spin_icon = qta.icon('fa5s.spinner', color='#FFC857', animation=qta.Spin(self.status_icon))
        self.status_icon.setPixmap(spin_icon.pixmap(16,16))

    def finish_scan(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0) # Chờ sao chép để có tiến trình thật
        self.checkbox.setEnabled(True)
        self.status_icon.setPixmap(qta.icon('fa5s.check-circle', color='#32CD32').pixmap(16,16))

    def reset(self):
        self.checkbox.setChecked(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.clear_speed()
        self.description_label.setProperty("status", "")
        self.description_label.style().polish(self.description_label)
        self.status_icon.clear()

    def show_ejected_status(self):
        self.checkbox.setEnabled(False)
        self.description_label.setText("✔ Đã tháo an toàn")
        self.description_label.setProperty("status", "success")
        self.description_label.style().polish(self.description_label)
        self.progress_bar.setValue(100)
        self.clear_speed()
        self.status_icon.setPixmap(qta.icon('fa5s.check-circle', color='#32CD32').pixmap(16,16))

    def update_speed(self, speed_mbps):
        if speed_mbps is not None:
            self.speed_label.setText(f"{speed_mbps:.1f} MB/s")

    def clear_speed(self):
        self.speed_label.setText("")

# --- Main Application Window (Phiên bản màu mè) ---
class AutoCopierApp(QMainWindow):
    log_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        
        self.icons = {
            "app_icon": qta.icon('fa5s.rocket', color='#FF8C00'),
            "folder": qta.icon('fa5s.folder-open', color='#DCE1E8'),
            "start": qta.icon('fa5s.play-circle', color_off='#FFFFFF'),
            "refresh": qta.icon('fa5s.sync-alt', color='#DCE1E8')
        }
        
        self.setWindowTitle("Auto Copier Pro ✨")
        self.setGeometry(100, 100, 1366, 768)
        self.setWindowIcon(self.icons["app_icon"])

        # --- App State Variables ---
        self.destination_path, self.delete_after_copy, self.is_auto_mode = "", False, False
        self.file_extensions, self.conflict_policy = "", ""
        self.kafka_servers, self.kafka_topic = "", ""
        
        self.detected_drives, self.video_item_map = {}, {}
        self.selected_drives, self.drive_widgets = set(), {}
        self.active_copy_processes, self.batch_results = 0, []
        self.log_signal.connect(self.log_message)
        self.kafka_manager = KafkaManager(app_logger_callback=self.log_signal.emit)
        self.copy_threads = {}

        self.load_app_config()
        self.create_widgets()
        self.setup_treeview()
        self.kafka_manager.configure_producer(self.kafka_servers)
        
        self.start_drive_monitor()
        self.update_drive_list()
        self._update_ui_states()

    def create_widgets(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_left_panel(main_layout)
        self._create_right_panel(main_layout)

    def _apply_glow_effect(self, widget, color=QColor(30, 144, 255, 90)):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    def _create_left_panel(self, master_layout):
        left_container = QFrame()
        left_container.setObjectName("LeftPanel")
        left_container.setFixedWidth(420)
        
        panel_layout = QVBoxLayout(left_container)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(20)

        self._create_settings_panel(panel_layout)
        self._create_drive_panel(panel_layout)

        master_layout.addWidget(left_container)

    def _create_right_panel(self, master_layout):
        right_container = QFrame()
        right_container.setObjectName("RightPanel")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 20, 20, 20)
        right_layout.setSpacing(15)

        splitter = QSplitter(Qt.Orientation.Vertical)
        
        file_list_frame = self._create_file_list_panel()
        log_frame = self._create_log_panel()

        splitter.addWidget(file_list_frame)
        splitter.addWidget(log_frame)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        right_layout.addWidget(splitter)
        master_layout.addWidget(right_container, 1)

    def _create_drive_panel(self, master_layout):
        drive_frame = QFrame()
        drive_layout = QVBoxLayout(drive_frame)
        drive_layout.setContentsMargins(0,0,0,0); drive_layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Thiết Bị & Ổ Đĩa"))
        header_layout.addStretch()
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(self.icons['refresh'])
        self.refresh_button.setObjectName("IconButton")
        self.refresh_button.setToolTip("Làm mới danh sách ổ đĩa")
        self.refresh_button.clicked.connect(self.update_drive_list)
        header_layout.addWidget(self.refresh_button)
        drive_layout.addLayout(header_layout)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("DriveScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.drive_list_widget = QWidget()
        self.drive_list_layout = QVBoxLayout(self.drive_list_widget)
        self.drive_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.drive_list_layout.setSpacing(0)
        
        scroll_area.setWidget(self.drive_list_widget)
        drive_layout.addWidget(scroll_area, 1)
        
        master_layout.addWidget(drive_frame, 1)

    def _create_settings_panel(self, master_layout):
        settings_frame = QFrame()
        layout = QVBoxLayout(settings_frame)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(15)

        dest_group = QFrame(); dest_group.setObjectName("SettingsGroup")
        dest_layout = QGridLayout(dest_group)
        dest_layout.addWidget(QLabel("<b>Thư Mục Đích</b>"), 0, 0, 1, 2)
        self.dest_entry = QLineEdit(self.destination_path)
        self.dest_entry.setPlaceholderText("Chọn thư mục lưu file..."); self.dest_entry.setReadOnly(True)
        dest_layout.addWidget(self.dest_entry, 1, 0)
        browse_button = QPushButton(); browse_button.setIcon(self.icons['folder'])
        browse_button.setObjectName("IconButton"); browse_button.setFixedWidth(40)
        browse_button.clicked.connect(self.browse_destination)
        dest_layout.addWidget(browse_button, 1, 1)
        layout.addWidget(dest_group)

        copy_group = QFrame(); copy_group.setObjectName("SettingsGroup")
        copy_layout = QGridLayout(copy_group); copy_layout.setSpacing(8)
        copy_layout.addWidget(QLabel("<b>Tùy Chỉnh Sao Chép</b>"), 0, 0, 1, 2)
        copy_layout.addWidget(QLabel("Loại file:"), 1, 0)
        self.ext_entry = QLineEdit(self.file_extensions)
        self.ext_entry.textChanged.connect(self.save_app_config)
        copy_layout.addWidget(self.ext_entry, 1, 1)
        copy_layout.addWidget(QLabel("Khi file trùng:"), 2, 0)
        self.conflict_menu = QComboBox(); self.conflict_menu.addItems(["Bỏ Qua", "Ghi Đè", "Đổi Tên"])
        self.conflict_menu.setCurrentText(self.conflict_policy)
        self.conflict_menu.currentTextChanged.connect(self.save_app_config)
        copy_layout.addWidget(self.conflict_menu, 2, 1)
        layout.addWidget(copy_group)

        action_group = QFrame(); action_group.setObjectName("SettingsGroup")
        action_layout = QVBoxLayout(action_group); action_layout.setSpacing(12)
        
        mode_layout = QHBoxLayout()
        self.mode_switch = QCheckBox("Chế Độ Tự Động")
        self.mode_switch.stateChanged.connect(self.toggle_auto_mode)
        self.delete_checkbox = QCheckBox("Xóa sạch thẻ sau khi chép")
        self.delete_checkbox.stateChanged.connect(lambda state: setattr(self, 'delete_after_copy', state == Qt.CheckState.Checked.value))
        mode_layout.addWidget(self.mode_switch); mode_layout.addStretch()
        mode_layout.addWidget(self.delete_checkbox)
        action_layout.addLayout(mode_layout)

        select_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Chọn Tất Cả"); self.select_all_button.clicked.connect(self.select_all_videos)
        self.deselect_all_button = QPushButton("Bỏ Chọn"); self.deselect_all_button.clicked.connect(self.deselect_all_videos)
        select_layout.addWidget(self.select_all_button); select_layout.addWidget(self.deselect_all_button)
        action_layout.addLayout(select_layout)

        self.copy_button = QPushButton("BẮT ĐẦU SAO CHÉP")
        self.copy_button.setIcon(self.icons['start']); self.copy_button.setObjectName("CopyButton")
        self.copy_button.clicked.connect(self.start_manual_copy)
        self._apply_glow_effect(self.copy_button, color=QColor(255, 140, 0, 100))
        action_layout.addWidget(self.copy_button)

        self._create_progress_frame(action_layout)
        layout.addWidget(action_group)
        
        self._apply_glow_effect(dest_group)
        self._apply_glow_effect(copy_group)
        self._apply_glow_effect(action_group)
        
        master_layout.addWidget(settings_frame)

    def _create_file_list_panel(self):
        c = QFrame(); layout = QVBoxLayout(c)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(10)
        layout.addWidget(QLabel("Danh Sách Tệp Tin"))
        self.video_tree = QTreeWidget(); layout.addWidget(self.video_tree, 1)
        return c

    def _create_log_panel(self):
        c = QFrame(); layout = QVBoxLayout(c)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(10)
        layout.addWidget(QLabel("Nhật Ký Hoạt Động"))
        self.log_textbox = QTextEdit()
        self.log_textbox.setReadOnly(True); self.log_textbox.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_textbox, 1)
        return c

    def _create_progress_frame(self, master_layout):
        self.progress_frame = QFrame()
        layout = QVBoxLayout(self.progress_frame); layout.setContentsMargins(0,8,0,0)
        self.progress_status_label = QLabel("Sẵn sàng")
        self.progress_bar = QProgressBar(); self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_status_label); layout.addWidget(self.progress_bar)
        master_layout.addWidget(self.progress_frame)
        self.progress_frame.hide()

    def setup_treeview(self):
        h = ["Trạng Thái", "Tên Tệp", "Kích Thước", "Thiết Bị", "Thời Gian", "Tiến Trình"]
        self.video_tree.setColumnCount(len(h)); self.video_tree.setHeaderLabels(h)
        self.video_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.video_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.video_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.video_tree.setAlternatingRowColors(True)

    # --- Core Logic and Event Handlers (Giữ nguyên) ---
    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {"INFO": "#8A93A0", "SUCCESS": "#32CD32", "WARN": "#FFC857", "ERROR": "#F87171", "CRITICAL": "#F87171"}
        color = color_map.get(level, "#8A93A0")
        formatted_message = f'<span style="color: #6A73A0;">[{timestamp}]</span> <b style="color: {color};">[{level}]</b>: <span style="color: #DCE1E8;">{message}</span>'
        self.log_textbox.append(formatted_message)

    def start_drive_monitor(self):
        self.monitor_thread = QThread(); self.drive_monitor = DriveMonitor()
        self.drive_monitor.moveToThread(self.monitor_thread)
        self.drive_monitor.drives_changed.connect(self.on_drives_changed)
        self.drive_monitor.log.connect(self.log_message)
        self.monitor_thread.started.connect(self.drive_monitor.run)
        self.monitor_thread.start()

    def on_drives_changed(self):
        current_mountpoints = {d.mountpoint for d in drive_manager.get_removable_drives()}
        existing_mountpoints = set(self.drive_widgets.keys())
        new_drives = current_mountpoints - existing_mountpoints
        self.update_drive_list()
        if self.is_auto_mode:
            for mountpoint in new_drives:
                 self.log_message(f"Tự động: Phát hiện thẻ mới {mountpoint}. Bắt đầu xử lý.", "INFO")
                 self.start_auto_process(mountpoint)

    def toggle_auto_mode(self, state):
        self.is_auto_mode = (state == Qt.CheckState.Checked.value)
        self.log_message(f"Chế độ TỰ ĐỘNG đã được {'BẬT' if self.is_auto_mode else 'TẮT'}.", "INFO")
        if self.is_auto_mode:
            for widget in self.drive_widgets.values():
                if widget.checkbox.isChecked(): widget.reset()
            self.selected_drives.clear(); self.clear_video_list()
            self.log_message(f"Tự động: Bắt đầu xử lý {len(self.drive_widgets)} thẻ hiện có...", "INFO")
            for mountpoint in self.drive_widgets.keys(): self.start_auto_process(mountpoint)
        self._update_ui_states()

    def update_drive_list(self):
        current_drives = drive_manager.get_removable_drives()
        current_mountpoints = {d.mountpoint for d in current_drives}
        existing_mountpoints = set(self.drive_widgets.keys())

        for mountpoint in existing_mountpoints - current_mountpoints:
            widget = self.drive_widgets.pop(mountpoint); widget.deleteLater()
            if mountpoint in self.selected_drives:
                self.selected_drives.remove(mountpoint)
                self.clear_video_list_for_drive(mountpoint)

        for drive in current_drives:
            if drive.mountpoint not in self.drive_widgets:
                try: total_gb = psutil.disk_usage(drive.mountpoint).total / (1024**3)
                except Exception: total_gb = 0
                widget = DriveWidget(drive.mountpoint, drive.fstype, total_gb)
                widget.selection_changed.connect(self.on_drive_selection_changed)
                self.drive_list_layout.addWidget(widget)
                self.drive_widgets[drive.mountpoint] = widget

        self.detected_drives = {d.mountpoint: {'device': d.device, 'description': d.opts} for d in current_drives}
        self._update_ui_states()

    def on_drive_selection_changed(self, mountpoint, is_selected):
        if self.is_auto_mode: return
        if is_selected:
            if mountpoint not in self.selected_drives:
                self.selected_drives.add(mountpoint)
                widget = self.drive_widgets.get(mountpoint)
                if widget: widget.start_scan()
                extensions = self.ext_entry.text()
                threading.Thread(target=self.list_videos_from_drive, args=(mountpoint, extensions), daemon=True).start()
        else:
            if mountpoint in self.selected_drives:
                self.selected_drives.remove(mountpoint)
                self.clear_video_list_for_drive(mountpoint)
        self._update_ui_states()

    def list_videos_from_drive(self, drive_path, extensions):
        self.log_signal.emit(f"Đang quét file trên {get_drive_name_from_mountpoint(drive_path)}...", "INFO")
        try:
            found_videos = list(file_operations.find_files_on_drive(drive_path, extensions))
            QApplication.instance().postEvent(self, CustomEvent("populate_list", drive_path=drive_path, videos=found_videos))
        except Exception as e:
            self.log_signal.emit(f"Lỗi khi quét file trên {drive_path}: {e}", "ERROR")

    def customEvent(self, event):
        if event.type() == CustomEvent.type():
            if event.event_id == "populate_list": self._populate_list_after_scan(event.drive_path, event.videos)
            elif event.event_id == "start_auto_copy": self._populate_and_start_auto_copy(event.mountpoint, event.videos)
    
    def _populate_list_after_scan(self, drive_path, found_videos):
        if drive_path in self.drive_widgets: self.drive_widgets[drive_path].finish_scan()
        if not found_videos: self.log_message(f"Không tìm thấy file video nào trên {get_drive_name_from_mountpoint(drive_path)}.", "WARN")
        else:
            self.video_tree.setUpdatesEnabled(False)
            new_items = [self.add_video_to_list(v) for v in found_videos if v]
            self.video_tree.setUpdatesEnabled(True)
            for item in new_items: item.setSelected(True)
        self._update_ui_states()

    def add_video_to_list(self, video_data):
        try:
            size_mb = video_data['size'] / (1024*1024)
            drive_name = get_drive_name_from_mountpoint(video_data.get('drive', 'N/A'))
            item = QTreeWidgetItem(["Sẵn sàng", os.path.basename(video_data['path']), f"{size_mb:.2f} MB", drive_name, "", ""])
            item_id = str(id(item))
            self.video_tree.addTopLevelItem(item)
            self.video_item_map[item_id] = { "item": item, "path": video_data['path'], "drive": video_data['drive'] }
            return item
        except Exception as e:
            self.log_message(f"Lỗi khi thêm video vào danh sách: {e}", "ERROR")
            return None

    def clear_video_list_for_drive(self, mountpoint_to_clear):
        items_to_remove = [(item_id, data['item']) for item_id, data in self.video_item_map.items() if data['drive'] == mountpoint_to_clear]
        for item_id, item in items_to_remove:
            (item.parent() or self.video_tree.invisibleRootItem()).removeChild(item)
            del self.video_item_map[item_id]
        self._update_ui_states()
        self.log_message(f"Đã xóa file từ {get_drive_name_from_mountpoint(mountpoint_to_clear)} khỏi danh sách.", "INFO")

    def _update_ui_states(self):
        is_copying = self.active_copy_processes > 0
        self.mode_switch.setEnabled(not is_copying)
        self.delete_checkbox.setEnabled(not self.is_auto_mode and not is_copying)
        if self.is_auto_mode: self.delete_checkbox.setChecked(True); self.delete_checkbox.setEnabled(False)
        for widget in self.drive_widgets.values(): widget.checkbox.setEnabled(not self.is_auto_mode and not is_copying)
        can_select = self.video_tree.topLevelItemCount() > 0 and not self.is_auto_mode and not is_copying
        self.select_all_button.setEnabled(can_select); self.deselect_all_button.setEnabled(can_select)
        has_selection = len(self.video_tree.selectedItems()) > 0
        self.copy_button.setEnabled(has_selection and not self.is_auto_mode and not is_copying)
    
    def closeEvent(self, event):
        self.log_message("Đang đóng ứng dụng...", "INFO")
        for thread, worker in list(self.copy_threads.values()):
            if thread.isRunning(): worker.stop(); thread.quit(); thread.wait(2000)
        if hasattr(self, 'monitor_thread') and self.monitor_thread.isRunning():
            self.drive_monitor.stop(); self.monitor_thread.quit(); self.monitor_thread.wait(5000)
        event.accept()

    def load_app_config(self):
        conf = config.load_config()
        self.destination_path = conf.get("destination_path", "")
        self.file_extensions = conf.get("video_extensions", config.DEFAULT_VIDEO_EXTENSIONS)
        self.conflict_policy = conf.get("conflict_policy", config.DEFAULT_CONFLICT_POLICY)
        self.kafka_servers = conf.get("kafka_servers", config.DEFAULT_KAFKA_SERVERS)
        self.kafka_topic = conf.get("kafka_topic", config.DEFAULT_KAFKA_TOPIC)

    def save_app_config(self):
        config.save_config({
            "destination_path": self.destination_path,
            "video_extensions": self.ext_entry.text(),
            "conflict_policy": self.conflict_menu.currentText()
        })

    def browse_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn Thư Mục Đích")
        if folder: self.destination_path = folder; self.dest_entry.setText(folder); self.save_app_config()
    
    def select_all_videos(self): self.video_tree.selectAll(); self._update_ui_states()
    def deselect_all_videos(self): self.video_tree.clearSelection(); self._update_ui_states()
    
    def start_manual_copy(self):
        selected_items = self.video_tree.selectedItems()
        if not selected_items: QMessageBox.warning(self, "Chưa chọn file", "Vui lòng chọn ít nhất một file để sao chép."); return
        if not self.destination_path: QMessageBox.warning(self, "Chưa chọn đích", "Vui lòng chọn thư mục đích."); return

        videos_by_drive = {}
        for item in selected_items:
            item_id = str(id(item))
            if item_id in self.video_item_map:
                video_info = self.video_item_map[item_id]
                mountpoint = video_info['drive']
                videos_by_drive.setdefault(mountpoint, []).append((video_info, item))

        if self.delete_after_copy:
            drive_names = ", ".join([get_drive_name_from_mountpoint(mp) for mp in videos_by_drive.keys()])
            if QMessageBox.question(self, "Xác Nhận Xóa", f"Bạn chắc chắn muốn XÓA TOÀN BỘ DỮ LIỆU trên các thẻ ({drive_names}) sau khi sao chép thành công?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return

        for mountpoint, pairs in videos_by_drive.items():
            videos = [p[0] for p in pairs]; ids = [str(id(p[1])) for p in pairs]
            self.start_copy_process(mountpoint, videos, ids)

    def start_auto_process(self, mountpoint):
        if not self.is_auto_mode: return
        widget = self.drive_widgets.get(mountpoint)
        if widget: widget.start_scan()
        extensions = self.ext_entry.text()
        threading.Thread(target=self._auto_process_thread, args=(mountpoint, extensions), daemon=True).start()

    def _auto_process_thread(self, mountpoint, extensions):
        try:
            self.log_signal.emit(f"Tự động: Đang quét {mountpoint}...", "INFO")
            videos = list(file_operations.find_files_on_drive(mountpoint, extensions))
            QApplication.instance().postEvent(self, CustomEvent("start_auto_copy", mountpoint=mountpoint, videos=videos))
        except Exception as e: self.log_signal.emit(f"Lỗi khi tự động quét {mountpoint}: {e}", "ERROR")

    def _populate_and_start_auto_copy(self, mountpoint, videos):
        widget = self.drive_widgets.get(mountpoint)
        if widget: widget.finish_scan()
        if not videos: self.log_message(f"Tự động: Không tìm thấy file trên {mountpoint}.", "INFO"); self._start_eject_drive(mountpoint); return
        item_ids = [str(id(self.add_video_to_list(v))) for v in videos if v]
        self.log_message(f"Tự động: Tìm thấy {len(videos)} file. Bắt đầu sao chép.", "INFO")
        self.start_copy_process(mountpoint, videos, item_ids)

    def start_copy_process(self, mountpoint, videos, item_ids):
        if not self.destination_path or not os.path.isdir(self.destination_path): QMessageBox.critical(self, "Lỗi", "Vui lòng chọn thư mục đích hợp lệ."); return
        required_space = file_operations.get_required_space([v['path'] for v in videos])
        if not file_operations.has_enough_space(self.destination_path, required_space): QMessageBox.critical(self, "Thiếu Dung Lượng", "Không đủ dung lượng trống tại thư mục đích."); return

        self.progress_frame.show(); self.progress_bar.setValue(0); self.progress_status_label.setText("Chuẩn bị sao chép...")
        self.active_copy_processes += 1; self._update_ui_states()

        thread = QThread()
        worker = CopyWorker(videos, self.destination_path, self.delete_after_copy, item_ids, mountpoint, self.conflict_menu.currentText())
        worker.moveToThread(thread)
        worker.signals.finished.connect(self._finalize_copy_process)
        worker.signals.progress.connect(self.update_overall_progress)
        worker.signals.file_status.connect(self.update_item_status)
        worker.signals.file_time.connect(self.update_item_time)
        worker.signals.log.connect(self.log_message)
        thread.started.connect(worker.run); thread.start()
        self.copy_threads[mountpoint] = (thread, worker)

    @Slot(int, int, str)
    def update_overall_progress(self, current, total, filename):
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.progress_status_label.setText(f"Đang xử lý {current}/{total}: {os.path.basename(filename)}")

    @Slot(str, str, str, object, object)
    def update_item_status(self, item_id, status_text, tag, progress_value, speed_mbps):
        if item_id in self.video_item_map:
            item_data = self.video_item_map[item_id]; item = item_data["item"]
            drive_mountpoint = item_data["drive"]
            if speed_mbps is not None and drive_mountpoint in self.drive_widgets: self.drive_widgets[drive_mountpoint].update_speed(speed_mbps)

            final_text, color = status_text, QColor("#DCE1E8")
            if tag == 'success': final_text, color = f"✔ {status_text}", QColor("#32CD32")
            elif tag == 'error': final_text, color = f"✖ {status_text}", QColor("#F87171")
            elif tag == 'processing': color = QColor("#FFC857")
            item.setText(0, final_text)
            for i in range(item.columnCount()): item.setForeground(i, color)

            if progress_value is not None and progress_value >= 0:
                bar = '█' * int(10 * progress_value) + '─' * (10 - int(10 * progress_value))
                item.setText(5, f"[{bar}] {int(progress_value * 100)}%")
            elif progress_value == -1.0: item.setText(5, "[LỖI]")
            
    @Slot(str, float)
    def update_item_time(self, item_id, duration):
        if item_id in self.video_item_map: self.video_item_map[item_id]["item"].setText(4, f"{duration:.2f} s")
            
    def _finalize_copy_process(self, results, mountpoint, copied_paths):
        drive_name = get_drive_name_from_mountpoint(mountpoint)
        self.batch_results.append({'drive_name': drive_name, 'results': results})
        if mountpoint in self.drive_widgets:
            self.drive_widgets[mountpoint].clear_speed()
            if results.get('error', 1) == 0: self._start_eject_drive(mountpoint)
        if mountpoint in self.copy_threads: thread, _ = self.copy_threads.pop(mountpoint); thread.quit(); thread.wait()
        self.active_copy_processes -= 1
        self.log_message(f"Hoàn tất cho {drive_name}. Thành công: {results.get('success', 0)}, Lỗi: {results.get('error', 0)}.", "SUCCESS" if results.get('error', 1) == 0 else "ERROR")
        if self.active_copy_processes == 0: self.progress_frame.hide(); self.show_consolidated_report()
        if copied_paths: threading.Thread(target=self._send_kafka_message_thread, args=(copied_paths, drive_name), daemon=True).start()
        self._update_ui_states()
        
    def _start_eject_drive(self, mountpoint):
        threading.Thread(target=self._eject_drive_thread, args=(mountpoint,), daemon=True).start()

    def _eject_drive_thread(self, mountpoint):
        drive_name = get_drive_name_from_mountpoint(mountpoint)
        self.log_signal.emit(f"Đang tháo {drive_name}...", "INFO")
        drive_info = self.detected_drives.get(mountpoint)
        if not drive_info: self.log_signal.emit(f"Lỗi khi tháo {drive_name}: Không tìm thấy thông tin.", "ERROR"); return
        success, message = drive_manager.eject_drive(drive_info['device'])
        widget = self.drive_widgets.get(mountpoint)
        if success:
            self.log_signal.emit(f"Đã tháo thành công {drive_name}.", "SUCCESS")
            if widget: QApplication.instance().postEvent(widget, CustomEvent("ejected"))
        else: self.log_signal.emit(f"Lỗi khi tháo {drive_name}: {message}", "ERROR")

    def _send_kafka_message_thread(self, file_paths, drive_name):
        message = {'timestamp': datetime.now().isoformat(), 'source_app': 'AutoCopierApp', 'event_type': 'copy_complete', 'drive_name': drive_name, 'copied_files': file_paths, 'file_count': len(file_paths)}
        self.kafka_manager.send_message(self.kafka_topic, message)

    def show_consolidated_report(self):
        if not self.batch_results: return
        report = "Tổng Kết Quá Trình Sao Chép:\n\n" + "".join([f"--- Ổ đĩa: {res['drive_name']} ---\n  - Thành công: {res['results']['success']}\n  - Bỏ qua: {res['results']['skipped']}\n  - Lỗi: {res['results']['error']}\n\n" for res in self.batch_results])
        QMessageBox.information(self, "Hoàn Tất", report)
        self.batch_results.clear(); self.reset_for_next_session()

    def clear_video_list(self): self.video_tree.clear(); self.video_item_map.clear(); self._update_ui_states()
    def reset_for_next_session(self):
        self.log_message("Sẵn sàng cho phiên làm việc tiếp theo.", "INFO")
        self.clear_video_list(); self.selected_drives.clear()
        for widget in self.drive_widgets.values(): widget.reset()
        self._update_ui_states()

# Custom Event class
class CustomEvent(QEvent):
    _type = QEvent.Type(QEvent.registerEventType())
    def __init__(self, event_id, **data): super().__init__(self._type); self.event_id = event_id; [setattr(self, k, v) for k, v in data.items()]
    @staticmethod
    def type(): return CustomEvent._type

# Monkey patch để DriveWidget xử lý custom event
DriveWidget.customEvent = lambda self, event: (self.show_ejected_status() if event.type() == CustomEvent.type() and event.event_id == "ejected" else QWidget.customEvent(self, event))

# --- Main Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # --- Vibrant & Colorful Stylesheet ---
    app.setStyleSheet("""
        /* --- COLOR PALETTE ---
           BG: #161a21
           PANEL_BG: #1c202a
           CARD_BG: rgba(44, 49, 58, 0.8) /* Glassmorphism */
           CARD_BORDER: rgba(138, 147, 160, 0.3)
           TEXT_PRIMARY: #DCE1E8
           TEXT_SECONDARY: #8A93A0
           
           ACCENT_ORANGE: #FF8C00
           ACCENT_GREEN: #32CD32
           ACCENT_BLUE: #1E90FF
        */

        /* --- Main Window & Panels --- */
        #CentralWidget { 
            background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 1, fx: 0.5, fy: 0.5, stop: 0 #2a2e3a, stop: 1 #161a21);
        }
        #LeftPanel { 
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #232731, stop:1 #1c202a);
            border-right: 1px solid #2c313a; 
        }
        #RightPanel { background-color: transparent; }

        /* --- General Widgets --- */
        QWidget { color: #DCE1E8; font-family: "Inter", "Segoe UI", sans-serif; font-size: 13px; }
        QLabel { background-color: transparent; font-size: 14px; font-weight: 500; }
        b { color: #FFFFFF; font-weight: 600; }

        /* --- Group Boxes (Glassmorphism Cards) --- */
        #SettingsGroup {
            background-color: CARD_BG;
            border: 1px solid CARD_BORDER;
            border-radius: 12px;
            padding: 15px;
        }

        /* --- Buttons --- */
        QPushButton {
            background-color: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #4A505A, stop:1 #3A404A);
            color: #DCE1E8; border: 1px solid #4A505A;
            padding: 9px 16px; border-radius: 8px; font-weight: 600;
        }
        QPushButton:hover { background-color: #4A505A; border-color: #1E90FF; }
        QPushButton:pressed { background-color: #3A404A; }
        QPushButton:disabled { background-color: #2c313a; color: #6A73A0; border-color: #3A404A; }
        
        #IconButton { background: transparent; border: none; }
        
        #CopyButton { 
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #FF8C00, stop:1 #FFA500);
            color: #FFFFFF; border: none; font-size: 15px; padding: 12px;
        }
        #CopyButton:hover { background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #FFA500, stop:1 #FFB733); }
        #CopyButton:pressed { background-color: #FF8C00; }
        #CopyButton:disabled { background-color: #2c313a; color: #6A73A0; }

        /* --- Checkboxes & Inputs --- */
        QCheckBox::indicator {
            width: 18px; height: 18px; border-radius: 6px; border: 2px solid #3A404A;
        }
        QCheckBox::indicator:hover { border-color: #1E90FF; }
        QCheckBox::indicator:checked { background-color: #1E90FF; border-color: #1E90FF; }
        
        QLineEdit, QComboBox {
            background: #2C313A; color: #DCE1E8;
            border: 1px solid #3A404A; border-radius: 6px; padding: 7px;
        }
        QLineEdit:focus, QComboBox:focus { border: 1px solid #1E90FF; }
        QComboBox QAbstractItemView { background: #2C313A; selection-background-color: #1E90FF; }

        /* --- Progress Bars --- */
        QProgressBar { background: #2C313A; border-radius: 8px; height: 16px; }
        QProgressBar::chunk { 
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1E90FF, stop:1 #32CD32);
            border-radius: 7px; 
        }
        
        /* --- Drive Widget Specific --- */
        QFrame#DriveWidgetFrame {
            background-color: #2C313A;
            border: 2px solid #3A404A; border-radius: 8px;
        }
        QFrame#DriveWidgetFrame[checked="true"] {
            border: 2px solid transparent;
            border-image: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E90FF, stop:1 #32CD32) 1;
        }
        #DriveNameLabel { font-size: 15px; }
        #DriveDescLabel { color: #8A93A0; }
        #DriveDescLabel[status="success"] { color: #32CD32; font-weight: bold; }
        #DriveSpeedLabel { color: #32CD32; font-weight: 600; }
        #DriveProgressBar { background-color: transparent; border: none; border-radius: 2px; }
        #DriveProgressBar::chunk { border-radius: 2px; background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1E90FF, stop:1 #32CD32); }

        /* --- QTree & QTextEdit --- */
        QTreeWidget, QTextEdit {
            background-color: rgba(28, 32, 42, 0.9);
            border: 1px solid #2c313a; border-radius: 8px;
            alternate-background-color: rgba(35, 39, 45, 0.9);
        }
        QHeaderView::section {
            background: transparent; border: none; border-bottom: 2px solid #2c313a; padding: 10px;
        }
        QTreeWidget::item:selected { 
            background: rgba(30, 144, 255, 0.2); 
            border-left: 3px solid #1E90FF;
            color: #FFFFFF;
        }
        QTreeWidget::item:hover { background: rgba(30, 144, 255, 0.1); }
        
        /* --- Scrollbars & Splitter --- */
        QScrollArea#DriveScrollArea { border: none; background: transparent; }
        QScrollBar:vertical { background: transparent; width: 10px; }
        QScrollBar::handle:vertical { background: #3A404A; min-height: 20px; border-radius: 5px; }
        QScrollBar::handle:vertical:hover { background: #4A505A; }
        QSplitter::handle { background-color: #2c313a; height: 2px; }
        QSplitter::handle:hover { background-color: #1E90FF; }
    """)
    
    window = AutoCopierApp()
    window.show()
    sys.exit(app.exec())