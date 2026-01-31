class ActionProvider {
  constructor(createChatBotMessage, setStateFunc) {
    this.createChatBotMessage = createChatBotMessage;
    this.setState = setStateFunc;
  }

  async handleUserInput = async (userInput) => {
    const res = await axios.post("http://localhost:5000/analyze", {
      text: userInput
    });
    
    if(res.data.sentiment === "NEGATIVE") {
      this.handleSad();
    }
  };

  handleSad = () => {
    const message = this.createChatBotMessage(
      "I notice you're feeling down. Would you like to:",
      { widget: "emergencyOptions" }
    );
    this.updateChatbotState(message);
  };

  updateChatbotState = (message) => {
    this.setState(prev => ({
      ...prev,
      messages: [...prev.messages, message]
    }));
  };
}

export default ActionProvider;