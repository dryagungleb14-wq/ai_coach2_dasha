"use client";

import { Evaluation } from "@/lib/api";

interface EvaluationTableProps {
  evaluation: Evaluation;
}

export default function EvaluationTable({ evaluation }: EvaluationTableProps) {
  const scores = evaluation.scores || {};
  
  const stageLabels: Record<string, string> = {
    "1.1": "1.1 Приветствие",
    "1.2": "1.2 Наличие техники",
    "2.1": "2.1 Выявление цели, боли",
    "2.2": "2.2 Критерии обучения",
    "3.1": "3.1 Запись на пробное",
    "3.2": "3.2 Повторная связь",
    "4.1": "4.1 Презентация формата",
    "4.2": "4.2 Презентация до пробного",
    "5.1": "5.1 Выявление возражений",
    "5.2": "5.2 Отработка возражений",
    "6": "6. Контрольные точки",
    "7": "7. Корректность сделки",
    "8": "8. Грамотность",
    "9": "9. Нарушения"
  };

  let comments: Record<string, string> = {};
  try {
    comments = JSON.parse(evaluation.комментарии || "{}");
  } catch {
    comments = {};
  }

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border border-gray-300 px-4 py-2 text-left">Этап</th>
            <th className="border border-gray-300 px-4 py-2 text-center">Балл</th>
            <th className="border border-gray-300 px-4 py-2 text-left">Комментарий</th>
          </tr>
        </thead>
        <tbody>
          {Object.keys(stageLabels).map((key) => {
            const scoreData = scores[key];
            const score = scoreData?.score || scoreData?.violation ? "Нарушение" : "-";
            const comment = comments[key] || scoreData?.comment || "";
            
            return (
              <tr key={key}>
                <td className="border border-gray-300 px-4 py-2">{stageLabels[key]}</td>
                <td className="border border-gray-300 px-4 py-2 text-center">{score}</td>
                <td className="border border-gray-300 px-4 py-2">{comment}</td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="bg-gray-50 font-semibold">
            <td className="border border-gray-300 px-4 py-2">Итоговая оценка</td>
            <td className="border border-gray-300 px-4 py-2 text-center">{evaluation.итоговая_оценка}</td>
            <td className="border border-gray-300 px-4 py-2">
              {evaluation.нарушения ? "Обнулено из-за нарушений" : ""}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}


