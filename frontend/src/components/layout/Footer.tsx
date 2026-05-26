import React from 'react'
import { Link } from 'react-router-dom'

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-green-900 text-white mt-16">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <h3 className="font-bold text-lg mb-4">Parentjobs</h3>
            <p className="text-green-100">
              Schnelle passende Jobs und Freelancer Tätigkeiten für Eltern im DACH-Raum.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-4">Für Arbeitnehmer</h4>
            <ul className="space-y-2 text-green-100">
              <li>
                <Link to="/jobs" className="hover:text-white transition">
                  Jobs durchsuchen
                </Link>
              </li>
              <li>
                <Link to="/register" className="hover:text-white transition">
                  Kostenlos registrieren
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-4">Für Arbeitgeber</h4>
            <ul className="space-y-2 text-green-100">
              <li>
                <Link to="/register" className="hover:text-white transition">
                  Inserate aufgeben
                </Link>
              </li>
              <li>
                <a href="#" className="hover:text-white transition">
                  Preise
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-4">Legal</h4>
            <ul className="space-y-2 text-green-100">
              <li>
                <a href="/terms" className="hover:text-white transition">
                  Nutzungsbedingungen
                </a>
              </li>
              <li>
                <a href="/privacy" className="hover:text-white transition">
                  Datenschutz
                </a>
              </li>
              <li>
                <a href="/imprint" className="hover:text-white transition">
                  Impressum
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-green-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-green-100">
              © {currentYear} Parentjobs. Alle Rechte vorbehalten.
            </p>
            <div className="flex gap-4 mt-4 md:mt-0">
              <a href="#" className="text-green-100 hover:text-white transition">
                Twitter
              </a>
              <a href="#" className="text-green-100 hover:text-white transition">
                LinkedIn
              </a>
              <a href="#" className="text-green-100 hover:text-white transition">
                Instagram
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
