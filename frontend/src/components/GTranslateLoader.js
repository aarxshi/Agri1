'use client'

import { useEffect } from 'react'

export default function GTranslateLoader() {
    useEffect(() => {
        // Create the inline script for gtranslateSettings
        const gtranslateSettingsScript = document.createElement('script')
        gtranslateSettingsScript.innerHTML = `
      window.gtranslateSettings = {
        default_language: "en",
        detect_browser_language: true,
        wrapper_selector: ".gtranslate_wrapper",
        languages: [
          "en", // English
          "hi", // Hindi
          "bn", // Bengali
          "te", // Telugu
          "mr", // Marathi
          "ta", // Tamil
          "ur", // Urdu
          "gu", // Gujarati
          "kn", // Kannada
          "pa", // Punjabi
          "ml", // Malayali
          "ne", // Nepali
          "sd", // Sindhi
          "sa", // Sanskrit (limited support)
          "kok", // Konkani (limited support)
          "mni", // Manipuri (limited support)
          "doi", // Dogri (limited support)
          "ks", // Kashmiri (limited support)
          "sat"  // Santali (limited support)
        ],
        flag_style: "3d",
        switcher_horizontal_position: "left",
        switcher_vertical_position: "bottom"
      };
    `
        document.body.appendChild(gtranslateSettingsScript)

        // Load the Google Translate widget script
        const gtranslateLibraryScript = document.createElement('script')
        gtranslateLibraryScript.src =
            'https://cdn.gtranslate.net/widgets/latest/float.js'
        gtranslateLibraryScript.defer = true
        document.body.appendChild(gtranslateLibraryScript)

        return () => {
            document.body.removeChild(gtranslateSettingsScript)
            document.body.removeChild(gtranslateLibraryScript)
        }
    }, [])

    return null
}