/**
 * RegisterPage — Seller Registration page.
 *
 * Allows a new seller to enter their personal details and select a
 * Group Leader + Bookstore combination from the lookup dropdown.
 * On success, redirects to /inventory.
 *
 * Route: /register
 */

import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookRover } from '../types';
import { useGroupLeaderLookup } from '../hooks/useGroupLeaderLookup';
import { registerSeller } from '../services/sellerService';

const MAX_NAME_LENGTH = 50;

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const { options, isLoading: lookupLoading, error: lookupError } = useGroupLeaderLookup();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [selectedOptionIndex, setSelectedOptionIndex] = useState<number | ''>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const selectedOption: BookRover.RegistrationDropdownOption | null =
    selectedOptionIndex !== '' ? options[selectedOptionIndex] : null;

  const isFormValid = useMemo(
    () =>
      firstName.trim().length > 0 &&
      lastName.trim().length > 0 &&
      isValidEmail(email) &&
      selectedOption !== null,
    [firstName, lastName, email, selectedOption],
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isFormValid || !selectedOption) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const seller = await registerSeller({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        group_leader_id: selectedOption.group_leader_id,
        bookstore_id: selectedOption.bookstore_id,
      });
      localStorage.setItem('bookrover_seller_id', seller.seller_id);
      navigate('/inventory');
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Registration failed. Please try again.';
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-start px-4 py-10">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-brand font-semibold text-blue-600">BookRover</h1>
          <p className="mt-1 text-base text-gray-500">Create your seller profile</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-6">Seller Registration</h2>

          {/* Lookup error (group leaders failed to load) */}
          {lookupError && (
            <div
              role="alert"
              className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm"
            >
              {lookupError}
            </div>
          )}

          {/* Submit error */}
          {submitError && (
            <div
              role="alert"
              className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm"
            >
              {submitError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            {/* First Name */}
            <div>
              <label
                htmlFor="first-name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                First Name <span className="text-red-500">*</span>
              </label>
              <input
                id="first-name"
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                maxLength={MAX_NAME_LENGTH}
                placeholder="Priya"
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Last Name */}
            <div>
              <label
                htmlFor="last-name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Last Name <span className="text-red-500">*</span>
              </label>
              <input
                id="last-name"
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                maxLength={MAX_NAME_LENGTH}
                placeholder="Sharma"
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email <span className="text-red-500">*</span>
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="priya@gmail.com"
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Group Leader + Bookstore dropdown */}
            <div>
              <label
                htmlFor="group-leader"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Group Leader &amp; Bookstore <span className="text-red-500">*</span>
              </label>

              {lookupLoading ? (
                <p className="text-sm text-gray-500 py-2">Loading groups…</p>
              ) : options.length === 0 ? (
                <p className="text-sm text-red-600 py-2">
                  No groups are set up yet. Contact your admin.
                </p>
              ) : (
                <select
                  id="group-leader"
                  value={selectedOptionIndex}
                  onChange={(e) =>
                    setSelectedOptionIndex(e.target.value === '' ? '' : Number(e.target.value))
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-base text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select a group leader and bookstore</option>
                  {options.map((option, index) => (
                    <option key={`${option.group_leader_id}-${option.bookstore_id}`} value={index}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Register button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={!isFormValid || isSubmitting}
                className="w-full min-h-[44px] rounded-lg bg-blue-600 text-white font-semibold text-base px-4 py-2.5 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Registering…' : 'Register'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
