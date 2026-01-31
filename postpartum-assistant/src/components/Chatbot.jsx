handleUserMessage = async (userInput) => {
  try {
    const response = await axios.post(
      "http://localhost:5000/analyze",
      { text: userInput },
      { headers: { "Content-Type": "application/json" } }
    );
    
    // Use the response data
    const botReply = response.data.sentiment === "NEGATIVE"
      ? `I understand you're feeling down (${(response.data.confidence * 100).toFixed(1)}% certainty). Here are resources: [...]`
      : "Glad to hear you're doing well!";
    
    this.setState(/* update chat with botReply */);
  } catch (error) {
    console.error("API Error:", error);
  }
};