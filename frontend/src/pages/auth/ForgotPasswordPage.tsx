import React from 'react'
import { Link } from 'react-router-dom'

const ForgotPasswordPage: React.FC = () => {
  return (
    <div className="w-full max-w-md">
      <div className="bg-white p-8 rounded-lg shadow-lg border border-green-200">
        <div className="text-center mb-8">
          <div className="inline-block w-12 h-12 bg-green-600 rounded-full flex items-center justify-center text-white font-bold text-xl mb-4">
            P
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Passwort zurücksetzen</h1>
          <p className="text-gray-600 text-sm mt-2">Gib deine E-Mail ein um dein Passwort zurückzusetzen</p>
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

          <button
            type="submit"
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
          >
            E-Mail senden
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="text-green-600 hover:text-green-700 font-medium text-sm">
            ← Zurück zur Anmeldung
          </Link>
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordPage
