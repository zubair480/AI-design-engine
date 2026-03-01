import { useEffect, useRef, useState, useCallback } from 'react'
import { wsBase } from '../config'

export interface AgentEvent {
  event: string
  timestamp?: number
  [key: string]: any
}

interface UseWebSocketReturn {
  events: AgentEvent[]
  isConnected: boolean
  lastEvent: AgentEvent | null
  connect: (sessionId: string) => void
  disconnect: () => void
}

export function useWebSocket(): UseWebSocketReturn {
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<AgentEvent | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const connect = useCallback((sessionId: string) => {
    disconnect()
    setEvents([])
    setLastEvent(null)

    const base = wsBase()
    const url = `${base}/api/ws/${sessionId}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onmessage = (msg) => {
      try {
        const event: AgentEvent = JSON.parse(msg.data)
        setEvents(prev => [...prev, event])
        setLastEvent(event)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setIsConnected(false)
    }
  }, [disconnect])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return { events, isConnected, lastEvent, connect, disconnect }
}
