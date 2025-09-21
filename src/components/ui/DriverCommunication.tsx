import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Card } from './Card'
import { Button } from './Button'
import { Input } from './Input'
import { Modal } from './Modal'
import { useToast } from '../../hooks/useToast'

interface Message {
  id: number
  message: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  sender_id: number
  sender_name: string
  sender_type: 'driver' | 'dispatch' | 'admin'
  recipient_type: 'driver' | 'dispatch' | 'admin'
  created_at: string
  read_at?: string
  is_read: boolean
}

interface QuickMessage {
  id: string
  text: string
  icon: string
  priority: 'low' | 'medium' | 'high' | 'critical'
}

const quickMessages: QuickMessage[] = [
  {
    id: 'running_late',
    text: 'Running 5-10 minutes late due to traffic',
    icon: '⏰',
    priority: 'medium'
  },
  {
    id: 'breakdown',
    text: 'Vehicle breakdown - need immediate assistance',
    icon: '🚨',
    priority: 'critical'
  },
  {
    id: 'route_blocked',
    text: 'Route blocked - requesting alternate route',
    icon: '🚧',
    priority: 'high'
  },
  {
    id: 'passenger_issue',
    text: 'Passenger-related issue - need guidance',
    icon: '👥',
    priority: 'medium'
  },
  {
    id: 'break_request',
    text: 'Requesting break - will resume in 15 minutes',
    icon: '☕',
    priority: 'low'
  },
  {
    id: 'fuel_low',
    text: 'Fuel running low - need refueling instructions',
    icon: '⛽',
    priority: 'medium'
  },
  {
    id: 'weather_issue',
    text: 'Weather conditions affecting visibility/safety',
    icon: '🌧️',
    priority: 'high'
  },
  {
    id: 'all_clear',
    text: 'All systems normal - trip proceeding as planned',
    icon: '✅',
    priority: 'low'
  }
]

interface DriverCommunicationProps {
  driverId: number
  driverName: string
  onMessageSent?: (message: any) => void
  className?: string
}

export const DriverCommunication: React.FC<DriverCommunicationProps> = ({
  driverId,
  driverName,
  onMessageSent,
  className = ''
}) => {
  const { t } = useTranslation()
  const { showToast } = useToast()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [selectedPriority, setSelectedPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('medium')
  const [loading, setLoading] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [isTyping, setIsTyping] = useState(false)

  // Mock messages for demo
  useEffect(() => {
    const mockMessages: Message[] = [
      {
        id: 1,
        message: 'Good morning! Your shift starts in 30 minutes. Vehicle KA-05-HB-1234 is ready.',
        priority: 'medium',
        sender_id: 100,
        sender_name: 'Dispatch Center',
        sender_type: 'dispatch',
        recipient_type: 'driver',
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        read_at: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(),
        is_read: true
      },
      {
        id: 2,
        message: 'Acknowledged. Starting pre-trip inspection now.',
        priority: 'low',
        sender_id: driverId,
        sender_name: driverName,
        sender_type: 'driver',
        recipient_type: 'dispatch',
        created_at: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(),
        is_read: true
      },
      {
        id: 3,
        message: 'Traffic update: Heavy congestion on Outer Ring Road. Consider alternate route via Sarjapur Road.',
        priority: 'high',
        sender_id: 101,
        sender_name: 'Traffic Control',
        sender_type: 'dispatch',
        recipient_type: 'driver',
        created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        is_read: false
      }
    ]
    
    setMessages(mockMessages)
    setUnreadCount(mockMessages.filter(m => !m.is_read && m.sender_type !== 'driver').length)
  }, [driverId, driverName])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (messageText: string, priority: string) => {
    if (!messageText.trim()) return

    setLoading(true)
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const newMsg: Message = {
        id: Date.now(),
        message: messageText,
        priority: priority as any,
        sender_id: driverId,
        sender_name: driverName,
        sender_type: 'driver',
        recipient_type: 'dispatch',
        created_at: new Date().toISOString(),
        is_read: false
      }
      
      setMessages(prev => [...prev, newMsg])
      setNewMessage('')
      
      if (onMessageSent) {
        onMessageSent(newMsg)
      }
      
      showToast('Message sent to dispatch', 'success')
      
      // Simulate dispatch response after a delay
      setTimeout(() => {
        const response: Message = {
          id: Date.now() + 1,
          message: 'Message received. We\'ll get back to you shortly.',
          priority: 'low',
          sender_id: 100,
          sender_name: 'Dispatch Center',
          sender_type: 'dispatch',
          recipient_type: 'driver',
          created_at: new Date().toISOString(),
          is_read: false
        }
        
        setMessages(prev => [...prev, response])
        setUnreadCount(prev => prev + 1)
      }, 3000)
      
    } catch (error) {
      showToast('Failed to send message', 'error')
    } finally {
      setLoading(false)
    }
  }

  const sendQuickMessage = (quickMsg: QuickMessage) => {
    sendMessage(quickMsg.text, quickMsg.priority)
  }

  const markAsRead = () => {
    setMessages(prev => 
      prev.map(msg => 
        msg.sender_type !== 'driver' ? { ...msg, is_read: true, read_at: new Date().toISOString() } : msg
      )
    )
    setUnreadCount(0)
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'low':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const today = new Date()
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    }
    
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    }
    
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short'
    })
  }

  return (
    <>
      <Button
        onClick={() => {
          setIsOpen(true)
          markAsRead()
        }}
        className={`relative flex items-center gap-2 ${className}`}
        variant="outline"
      >
        <span className="text-lg">💬</span>
        Dispatch
        {unreadCount > 0 && (
          <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Dispatch Communication"
        size="lg"
      >
        <div className="flex flex-col h-[70vh]">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 bg-gray-50 dark:bg-gray-800 rounded-lg mb-4">
            <div className="space-y-4">
              {messages.map((message, index) => {
                const isOwnMessage = message.sender_type === 'driver'
                const showDate = index === 0 || 
                  formatDate(messages[index - 1].created_at) !== formatDate(message.created_at)
                
                return (
                  <div key={message.id}>
                    {showDate && (
                      <div className="text-center my-4">
                        <span className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-sm rounded-full">
                          {formatDate(message.created_at)}
                        </span>
                      </div>
                    )}
                    
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[80%] ${isOwnMessage ? 'order-2' : 'order-1'}`}>
                        <div className={`p-3 rounded-lg ${
                          isOwnMessage
                            ? 'bg-blue-600 text-white'
                            : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600'
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium">
                              {isOwnMessage ? 'You' : message.sender_name}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(message.priority)}`}>
                              {message.priority}
                            </span>
                          </div>
                          <p className="text-sm">{message.message}</p>
                          <div className="flex items-center justify-between mt-2">
                            <span className={`text-xs ${
                              isOwnMessage ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'
                            }`}>
                              {formatTime(message.created_at)}
                            </span>
                            {isOwnMessage && (
                              <span className="text-xs text-blue-200">
                                {message.read_at ? '✓✓' : '✓'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </div>
                )
              })}
              
              {isTyping && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-white dark:bg-gray-700 p-3 rounded-lg border border-gray-200 dark:border-gray-600">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Quick Messages */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quick Messages
            </h4>
            <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto">
              {quickMessages.map((quickMsg) => (
                <Button
                  key={quickMsg.id}
                  onClick={() => sendQuickMessage(quickMsg)}
                  variant="outline"
                  size="sm"
                  className="text-left justify-start h-auto py-2 px-3"
                  disabled={loading}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">{quickMsg.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs truncate">{quickMsg.text}</p>
                    </div>
                  </div>
                </Button>
              ))}
            </div>
          </div>

          {/* Message Input */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Priority:</span>
              <div className="flex gap-1">
                {['low', 'medium', 'high', 'critical'].map((priority) => (
                  <button
                    key={priority}
                    onClick={() => setSelectedPriority(priority as any)}
                    className={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${
                      selectedPriority === priority
                        ? getPriorityColor(priority)
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {priority}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex gap-2">
              <Input
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message to dispatch..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendMessage(newMessage, selectedPriority)
                  }
                }}
                className="flex-1"
              />
              <Button
                onClick={() => sendMessage(newMessage, selectedPriority)}
                disabled={loading || !newMessage.trim()}
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  'Send'
                )}
              </Button>
            </div>
          </div>
        </div>
      </Modal>
    </>
  )
}

export default DriverCommunication