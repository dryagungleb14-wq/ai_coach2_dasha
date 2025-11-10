const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace("http://", "ws://").replace("https://", "wss://");

export interface ProgressUpdate {
  call_id: number;
  progress: number;
  status: string;
  message?: string;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private callId: number;
  private onProgress: (update: ProgressUpdate) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(callId: number, onProgress: (update: ProgressUpdate) => void) {
    this.callId = callId;
    this.onProgress = onProgress;
  }

  connect(): void {
    try {
      const wsUrl = `${WS_URL}/ws/analyze/${this.callId}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`WebSocket подключен для звонка ${this.callId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: ProgressUpdate = JSON.parse(event.data);
          this.onProgress(data);
        } catch (error) {
          console.error("Ошибка парсинга WebSocket сообщения:", error);
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket ошибка:", error);
      };

      this.ws.onclose = () => {
        console.log(`WebSocket отключен для звонка ${this.callId}`);
        this.ws = null;
        this.attemptReconnect();
      };
    } catch (error) {
      console.error("Ошибка создания WebSocket соединения:", error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error("Достигнуто максимальное количество попыток переподключения");
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

