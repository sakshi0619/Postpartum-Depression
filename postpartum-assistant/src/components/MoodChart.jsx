import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

export default function MoodChart({ moodData }) {
  const data = {
    labels: moodData.map(entry => entry.date),
    datasets: [{
      label: 'Mood Level',
      data: moodData.map(entry => entry.score),
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1
    }]
  };
  return <Line data={data} />;
}