export default {
  botName: "Postpartum Helper",
  initialMessages: [
    { 
      message: "Hello! How are you feeling today?", 
      type: "text",
      widget: "moodSelector" 
    }
  ],
  widgets: [
    {
      widgetName: "moodSelector",
      widgetFunc: (props) => <MoodSelector {...props} />,
    }
  ]
};