import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

// Temporary test component
const Test = () => <h1 style={{color: 'red'}}>React is working!</h1>

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Test />
  </React.StrictMode>
)