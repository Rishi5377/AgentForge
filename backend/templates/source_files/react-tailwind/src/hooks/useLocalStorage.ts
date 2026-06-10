import { useState } from "react";

/**
 * A type-safe, crash-proof hook for managing localStorage.
 * It natively catches JSON parsing errors and legacy schema drifts
 * so the React app never crashes on boot.
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  // State to store our value
  // Pass initial state function to useState so logic is only executed once
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === "undefined") {
      return initialValue;
    }
    try {
      // Get from local storage by key
      const item = window.localStorage.getItem(key);
      if (!item) return initialValue;
      
      const parsed = JSON.parse(item);
      
      // Strict Array Validation: If initialValue is an array, the parsed data MUST be an array.
      // This prevents legacy objects from crashing `.map()` calls.
      if (Array.isArray(initialValue) && !Array.isArray(parsed)) {
        console.warn(`Type mismatch for key "${key}": expected Array. Falling back to initialValue.`);
        return initialValue;
      }
      
      return parsed;
    } catch (error) {
      // If error also return initialValue
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Return a wrapped version of useState's setter function that ...
  // ... persists the new value to localStorage.
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore =
        value instanceof Function ? value(storedValue) : value;
      // Save state
      setStoredValue(valueToStore);
      // Save to local storage
      if (typeof window !== "undefined") {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      // A more advanced implementation would handle the error case
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue] as const;
}
