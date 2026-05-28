import React, { useState } from 'react'
import { Link } from 'react-router-dom'

const RegisterPage: React.FC = () => {
  const [role, setRole] = useState<'employee' | 'employer'>('employee')

  return (
    <div className="w-full max-w-md">
      <div className="bg-white p-8 rounded-lg shadow-lg border border-green-200">
        <div className="text-center mb-8">
          <div className="inline-block w-12 h-12 bg-green-600 rounded-full flex items-center justify-center text-white font-bold text-xl mb-4">
            P
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Parentjobs</h1>
          <p className="text-gray-600 text-sm mt-2">Neues Konto erstellen</p>
        </div>

        {/* Role Selection */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={() => setRole('employee')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
              role === 'employee'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Arbeitnehmer
          </button>
          <button
            onClick={() => setRole('employer')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition ${
              role === 'employer'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Arbeitgeber
          </button>
        </div>

        <form className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">E-Mail</label>
            <input
              type="email"
              placeholder="deine@email.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Passwort</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Passwort wiederholen</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <label className="flex items-center gap-2">
            <input type="checkbox" className="w-4 h-4" required />
            <span className="text-sm text-gray-700">
              Ich akzeptiere die{' '}
              <a href="#" className="text-green-600 hover:text-green-700">
                Nutzungsbedingungen
              </a>
            </span>
          </label>

          <button
            type="submit"
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
          >
            Registrieren
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Bereits angemeldet?{' '}
            <Link to="/login" className="text-green-600 hover:text-green-700 font-medium">
              Hier anmelden
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
