const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Call {
  id: number;
  filename: string;
  manager?: string;
  call_date?: string;
  call_identifier?: string;
  created_at: string;
  evaluation?: {
    итоговая_оценка?: number;
    нарушения?: boolean;
  };
}

export interface CallDetail extends Call {
  transcription?: string;
  duration?: number;
  evaluations?: Evaluation[];
}

export interface Evaluation {
  id: number;
  scores: Record<string, any>;
  итоговая_оценка: number;
  нарушения: boolean;
  комментарии: string;
  is_retest: boolean;
  created_at: string;
}

export async function uploadFiles(
  files: File[],
  manager?: string,
  callDate?: string,
  callIdentifier?: string
): Promise<Call[]> {
  const formData = new FormData();
  
  files.forEach((file) => {
    formData.append("files", file);
  });
  
  if (manager) formData.append("manager", manager);
  if (callDate) formData.append("call_date", callDate);
  if (callIdentifier) formData.append("call_identifier", callIdentifier);
  
  try {
    const response = await fetch(`${API_URL}/api/upload`, {
      method: "POST",
      body: formData,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "Ошибка загрузки файлов";
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    return data.calls;
  } catch (error: any) {
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.");
    }
    throw error;
  }
}

export async function analyzeCall(callId: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/analyze/${callId}`, {
    method: "POST",
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Analysis failed: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getAnalyzeStatus(callId: number): Promise<{status: string, progress: number}> {
  const response = await fetch(`${API_URL}/api/analyze/${callId}/status`);
  
  if (!response.ok) {
    throw new Error(`Failed to get status: ${response.status}`);
  }
  
  return response.json();
}

export async function retestCall(callId: number): Promise<any> {
  const response = await fetch(`${API_URL}/api/analyze/${callId}/retest`, {
    method: "POST",
  });
  
  if (!response.ok) {
    throw new Error("Retest failed");
  }
  
  return response.json();
}

export async function getCalls(
  manager?: string,
  startDate?: string,
  endDate?: string
): Promise<Call[]> {
  try {
    const params = new URLSearchParams();
    if (manager) params.append("manager", manager);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const response = await fetch(`${API_URL}/api/calls?${params.toString()}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch calls: ${response.status}`);
    }
    
    const data = await response.json();
    return data.calls;
  } catch (error: any) {
    console.error("Error fetching calls:", error);
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.");
    }
    throw error;
  }
}

export async function getCall(callId: number): Promise<CallDetail> {
  try {
    const response = await fetch(`${API_URL}/api/calls/${callId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch call: ${response.status}`);
    }
    
    return response.json();
  } catch (error: any) {
    console.error("Error fetching call:", error);
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.");
    }
    throw error;
  }
}

export async function exportCall(callId: number): Promise<Blob> {
  try {
    const response = await fetch(`${API_URL}/api/export/${callId}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Export failed: ${response.status} - ${errorText}`);
    }
    
    return response.blob();
  } catch (error: any) {
    console.error("Error exporting call:", error);
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.");
    }
    throw error;
  }
}

export async function exportCalls(
  manager?: string,
  startDate?: string,
  endDate?: string
): Promise<Blob> {
  try {
    const params = new URLSearchParams();
    if (manager) params.append("manager", manager);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const response = await fetch(`${API_URL}/api/export?${params.toString()}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Export failed: ${response.status} - ${errorText}`);
    }
    
    return response.blob();
  } catch (error: any) {
    console.error("Error exporting calls:", error);
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен.");
    }
    throw error;
  }
}

