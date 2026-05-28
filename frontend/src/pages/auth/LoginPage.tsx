import React from 'react'
import { Link } from 'react-router-dom'

const LoginPage: React.FC = () => {
  return (
    <div className="w-full max-w-md">
      <div className="bg-white p-8 rounded-lg shadow-lg border border-green-200">
        <div className="text-center mb-8">
          <div className="inline-block w-12 h-12 bg-green-600 rounded-full flex items-center justify-center text-white font-bold text-xl mb-4">
            P
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Parentjobs</h1>
          <p className="text-gray-600 text-sm mt-2">Anmelden zu deinem Konto</p>
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

          <button
            type="submit"
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
          >
            Anmelden
          </button>
        </form>

        <div className="my-6 flex items-center">
          <div className="flex-1 border-t border-gray-300"></div>
          <div className="px-4 text-gray-500 text-sm">oder</div>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        <div className="space-y-2">
          <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium">
            Mit Google anmelden
          </button>
          <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium">
            Mit LinkedIn anmelden
          </button>
        </div>

        <div className="mt-6 text-center space-y-2">
          <Link to="/forgot-password" className="block text-sm text-green-600 hover:text-green-700">
            Passwort vergessen?
          </Link>
          <p className="text-sm text-gray-600">
            Noch kein Konto?{' '}
            <Link to="/register" className="text-green-600 hover:text-green-700 font-medium">
              Jetzt registrieren
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
