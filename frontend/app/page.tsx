"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import AudioUpload from "@/components/AudioUpload";
import { getCalls, Call } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [recentCalls, setRecentCalls] = useState<Call[]>([]);

  useEffect(() => {
    loadRecentCalls();
  }, []);

  const loadRecentCalls = async () => {
    try {
      const data = await getCalls();
      setRecentCalls(data.slice(0, 5));
    } catch (error: any) {
      console.error("Error loading calls:", error);
    }
  };

  const handleUploadComplete = () => {
    loadRecentCalls();
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="w-full max-w-6xl mx-auto p-6">
        <h1 className="text-3xl font-semibold mb-6">AI Coach - Анализ звонков</h1>

        <div className="mb-8">
          <AudioUpload onUploadComplete={handleUploadComplete} />
        </div>

        <div className="mb-4 flex gap-4">
          <button
            onClick={() => router.push("/history")}
            className="px-4 py-2 bg-gray-600 text-white rounded"
          >
            История звонков
          </button>
        </div>

        {recentCalls.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Последние звонки</h2>
            <div className="space-y-2">
              {recentCalls.map((call) => (
                <div
                  key={call.id}
                  className="p-4 border border-gray-200 rounded cursor-pointer hover:bg-gray-50"
                  onClick={() => router.push(`/calls/${call.id}`)}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{call.filename}</p>
                      <p className="text-sm text-gray-600">
                        {call.manager && `Менеджер: ${call.manager} • `}
                        {call.call_date && new Date(call.call_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      {call.evaluation?.итоговая_оценка !== undefined && (
                        <p className="font-semibold">
                          {call.evaluation.итоговая_оценка} баллов
                        </p>
                      )}
                      {call.evaluation?.нарушения && (
                        <p className="text-sm text-red-600">Нарушения</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
