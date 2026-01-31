class MessageParser {
  constructor(actionProvider) {
    this.actionProvider = actionProvider;
  }

  parse(message) {
    const lowerCase = message.toLowerCase();
    if (lowerCase.includes("sad")) {
      this.actionProvider.handleSad();
    }
    else if (lowerCase.includes("happy") || lowerCase.includes("good")) {
      this.actionProvider.handleHappy();
    }
    else {
      this.actionProvider.handleDefault();
    }
  }
}

export default MessageParser;