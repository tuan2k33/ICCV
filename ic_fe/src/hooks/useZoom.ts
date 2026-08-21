import { useCallback, useEffect, useRef, useState, type RefObject } from 'react'

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

export const useZoom = (
  wrapperRef: RefObject<HTMLElement | null>,
  targetRef: RefObject<HTMLElement | null>,
  zoom: {
    min: number
    max: number
    init: number
    step?: number
  },
) => {
  const [zoomScale, setZoomScale] = useState(zoom.init)
  const [translate, setTranslate] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const dragStart = useRef<{ x: number; y: number } | null>(null)

  useEffect(() => {
    if (!wrapperRef.current || !targetRef.current) return

    const abortController = new AbortController()

    wrapperRef.current.addEventListener('wheel', handleWheel, {
      signal: abortController.signal,
    })
    wrapperRef.current.addEventListener('mousedown', handleMouseDown, {
      signal: abortController.signal,
    })
    wrapperRef.current.addEventListener('mousemove', handleMouseMove, {
      signal: abortController.signal,
    })
    wrapperRef.current.addEventListener('mouseup', handleMouseUp, {
      signal: abortController.signal,
    })
    wrapperRef.current.addEventListener('mouseleave', handleMouseUp, {
      signal: abortController.signal,
    })

    return () => {
      abortController.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wrapperRef, targetRef, zoomScale, translate, isDragging])

  const handleResetZoom = useCallback(() => {
    setZoomScale(zoom.init)
    setTranslate({
      x: 0,
      y: 0,
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleWheel = (e: WheelEvent) => {
    e.preventDefault()
    const rect = wrapperRef.current!.getBoundingClientRect()
    const offsetX = e.clientX - rect.left
    const offsetY = e.clientY - rect.top

    let newScale =
      Math.round(clamp(zoomScale + e.deltaY * -(zoom.step || 0.002), zoom.min, zoom.max) * 100) /
      100

    const scaleFactor = newScale / zoomScale

    const newTranslate = {
      x: offsetX - scaleFactor * (offsetX - translate.x),
      y: offsetY - scaleFactor * (offsetY - translate.y),
    }

    setZoomScale(newScale)
    setTranslate(getClampedTranslate(newTranslate.x, newTranslate.y, newScale))
  }

  const handleMouseDown = (e: MouseEvent) => {
    setIsDragging(true)
    dragStart.current = { x: e.clientX - translate.x, y: e.clientY - translate.y }
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !dragStart.current) return

    const newTranslate = {
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y,
    }

    setTranslate(getClampedTranslate(newTranslate.x, newTranslate.y))
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    dragStart.current = null
  }

  const getClampedTranslate = (x: number, y: number, newZoomScale: number = zoomScale) => {
    const container = wrapperRef.current
    if (!container || !targetRef.current?.offsetWidth || !targetRef.current?.offsetHeight)
      return { x, y }

    const rect = container.getBoundingClientRect()
    const scaledWidth = targetRef.current?.offsetWidth * newZoomScale
    const scaledHeight = targetRef.current?.offsetHeight * newZoomScale

    const minX = Math.min(0, rect.width - scaledWidth)
    const minY = Math.min(0, rect.height - scaledHeight)

    let newY = clamp(y, minY, 0)
    let newX = clamp(x, minX, 0)

    const newTargetSize = {
      width: container.offsetWidth * newZoomScale,
      height: container.offsetHeight * newZoomScale,
    }

    const bottom = rect.top + newTargetSize.height + newY
    const right = rect.left + newTargetSize.width + newX

    if (bottom < rect.bottom) {
      newY += rect.bottom - bottom
    }

    if (right < rect.right) {
      newX += rect.right - right
    }

    return {
      x: newX,
      y: newY,
    }
  }

  return { zoomScale, translate, isDragging, handleResetZoom }
}
