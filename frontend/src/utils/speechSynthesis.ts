/**
 * Clinical Agent Speech Synthesis Utility (Web Speech API)
 * Provides authentic, role-tailored speech synthesis for virtual hospital specialists.
 */

export interface VoicePersona {
  name: string;
  role: string;
  pitch: number;
  rate: number;
  lang: string;
  preferredVoiceGender?: 'male' | 'female';
}

export const AGENT_VOICE_PERSONAS: Record<string, VoicePersona> = {
  DR_VANCE: {
    name: 'Dr. Marcus Vance, MD',
    role: 'Internal Medicine Specialist',
    pitch: 0.92,
    rate: 0.98,
    lang: 'en-US',
    preferredVoiceGender: 'male',
  },
  DR_ROSTOVA: {
    name: 'Dr. Elena Rostova, PharmD',
    role: 'Clinical Pharmacist Specialist',
    pitch: 1.05,
    rate: 1.0,
    lang: 'en-US',
    preferredVoiceGender: 'female',
  },
  NURSE_SARAH: {
    name: 'Sarah Jenkins, RN',
    role: 'Triage & Inpatient Nurse',
    pitch: 1.1,
    rate: 1.02,
    lang: 'en-US',
    preferredVoiceGender: 'female',
  },
  DAVID_CHEN: {
    name: 'David Chen, CLS',
    role: 'Laboratory Scientist',
    pitch: 1.0,
    rate: 1.04,
    lang: 'en-US',
    preferredVoiceGender: 'male',
  },
  DR_HAYES: {
    name: 'Dr. Arthur Hayes, MD',
    role: 'Radiology Specialist',
    pitch: 0.94,
    rate: 0.96,
    lang: 'en-US',
    preferredVoiceGender: 'male',
  },
  DR_LIN: {
    name: 'Dr. Sarah Lin, MD, FACS',
    role: 'Lead Attending Surgeon',
    pitch: 1.02,
    rate: 1.0,
    lang: 'en-US',
    preferredVoiceGender: 'female',
  },
  DR_RACHEL_VANCE: {
    name: 'Dr. Rachel Vance, MD, FACC',
    role: 'Attending Cardiologist',
    pitch: 1.05,
    rate: 1.0,
    lang: 'en-US',
    preferredVoiceGender: 'female',
  },
  DR_KIM: {
    name: 'Dr. David Kim, MD, FACEP',
    role: 'Lead Attending Physician, Emergency Medicine',
    pitch: 0.96,
    rate: 1.0,
    lang: 'en-US',
    preferredVoiceGender: 'male',
  },
};

let isMuted = false;
let currentUtterance: SpeechSynthesisUtterance | null = null;

export const isSpeechSupported = (): boolean => {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
};

export const isGlobalMuted = (): boolean => isMuted;

export const isCurrentlySpeaking = (): boolean => {
  return currentUtterance !== null && typeof window !== 'undefined' && window.speechSynthesis.speaking;
};


export const toggleGlobalMute = (forceState?: boolean): boolean => {
  isMuted = forceState !== undefined ? forceState : !isMuted;
  if (isMuted) {
    stopClinicalSpeech();
  }
  return isMuted;
};

export const stopClinicalSpeech = (): void => {
  if (isSpeechSupported()) {
    window.speechSynthesis.cancel();
    currentUtterance = null;
  }
};

export const speakClinicalMessage = (
  text: string,
  personaKey: keyof typeof AGENT_VOICE_PERSONAS = 'DR_VANCE',
  onStart?: () => void,
  onEnd?: () => void
): void => {
  if (!isSpeechSupported() || isMuted) {
    return;
  }

  stopClinicalSpeech();

  // Strip excessive markdown / citations for speech clarity
  const cleanedText = text
    .replace(/\[\^?\d+\]/g, '') // remove citation numbers
    .replace(/[#*_`]/g, '') // remove markdown symbols
    .replace(/\s+/g, ' ')
    .trim();

  if (!cleanedText) return;

  const persona = AGENT_VOICE_PERSONAS[personaKey] || AGENT_VOICE_PERSONAS.DR_VANCE;
  const utterance = new SpeechSynthesisUtterance(cleanedText);
  utterance.pitch = persona.pitch;
  utterance.rate = persona.rate;
  utterance.lang = persona.lang;

  // Best-effort voice matching
  const voices = window.speechSynthesis.getVoices();
  if (voices.length > 0) {
    const matchingVoice = voices.find((v) => {
      const vName = v.name.toLowerCase();
      if (persona.preferredVoiceGender === 'male') {
        return (
          v.lang.startsWith('en') &&
          (vName.includes('david') ||
            vName.includes('james') ||
            vName.includes('george') ||
            vName.includes('male') ||
            vName.includes('guy'))
        );
      } else {
        return (
          v.lang.startsWith('en') &&
          (vName.includes('zira') ||
            vName.includes('samantha') ||
            vName.includes('victoria') ||
            vName.includes('female') ||
            vName.includes('hazel'))
        );
      }
    });

    if (matchingVoice) {
      utterance.voice = matchingVoice;
    } else {
      const enVoice = voices.find((v) => v.lang.startsWith('en'));
      if (enVoice) utterance.voice = enVoice;
    }
  }

  utterance.onstart = () => {
    currentUtterance = utterance;
    if (onStart) onStart();
  };

  utterance.onend = () => {
    currentUtterance = null;
    if (onEnd) onEnd();
  };

  utterance.onerror = (e) => {
    console.warn('Speech synthesis error:', e);
    currentUtterance = null;
    if (onEnd) onEnd();
  };

  window.speechSynthesis.speak(utterance);
};
