import { useState } from "react";
import EncodeTab from "./components/EncodeTab";
import DecodeTab from "./components/DecodeTab";
import ReverseTab from "./components/ReverseTab";
import CompareTab from "./components/CompareTab";
import GenRSATab from "./components/GenRSATab";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faLock,
  faLockOpen,
  faRotateLeft,
  faChartBar,
  faKey,
} from "@fortawesome/free-solid-svg-icons";
import "./index.css";

function App() {
  const [activeTab, setActiveTab] = useState("encode");

  const tabs = [
    { id: "encode", label: "Encode", icon: faLock },
    { id: "decode", label: "Decode", icon: faLockOpen },
    { id: "reverse", label: "Reverse", icon: faRotateLeft },
    { id: "compare", label: "Compare", icon: faChartBar },
    { id: "genrsa", label: "Generate RSA", icon: faKey },
  ];

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <header className="bg-gradient-to-r from-primary-600 via-purple-600 to-secondary-600 text-white py-8 px-6 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-2 tracking-tight">
              CustomGANStego
            </h1>
            <p className="text-lg md:text-xl opacity-90 font-light">
              GAN-based Steganography with RSA Encryption
            </p>
          </header>

          {/* Tabs */}
          <div className="bg-gray-50 border-b-2 border-gray-200 overflow-x-auto">
            <div className="flex">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`flex-1 min-w-[140px] px-6 py-4 font-semibold text-sm md:text-base transition-all duration-200 whitespace-nowrap ${
                    activeTab === tab.id
                      ? "bg-white text-primary-600 border-b-4 border-primary-600 shadow-sm"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <FontAwesomeIcon icon={tab.icon} className="mr-2" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6 md:p-10 min-h-[600px] bg-gradient-to-br from-gray-50 to-white">
            {activeTab === "encode" && <EncodeTab />}
            {activeTab === "decode" && <DecodeTab />}
            {activeTab === "reverse" && <ReverseTab />}
            {activeTab === "compare" && <CompareTab />}
            {activeTab === "genrsa" && <GenRSATab />}
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center mt-8 text-white text-sm opacity-75">
          <p>CustomGANStego © 2025 - Secure Steganography Tool</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
