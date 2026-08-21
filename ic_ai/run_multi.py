import subprocess
import os
import time
os.environ["DECORD_EOF_RETRY_MAX"] = "20480000"
 
def run_mp(n):
    processes = []
    for i in range(n):
        os.environ['CUDA_VISIBLE_DEVICES'] = str(i%2)
        
        p = subprocess.Popen(['python', 'main.py'])
        time.sleep(5)
        processes.append(p)
    for p in processes:
        p.wait()
 
if __name__ == "__main__":
    start = time.time()
    num_process = int(input('Nhập số luồng bạn muốn chạy: '))
    run_mp(num_process)
    print(f'Time {num_process} process:', time.time() - start)