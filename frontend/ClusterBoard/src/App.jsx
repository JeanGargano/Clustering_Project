import { useState } from 'react'
import './App.css'
import Navbar from './sections/Navbar'
import Hero from './sections/Hero'
import FileUpload from './sections/Dragzone'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
    <Navbar />
    <Hero />
    <FileUpload />

      
    </>
  )
}

export default App
