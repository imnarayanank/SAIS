import { createClient } from '@supabase/supabase-js'

const url = (import.meta.env.VITE_SUPABASE_URL || '').trim()
const key = (import.meta.env.VITE_SUPABASE_ANON_KEY || '').trim()

export const supabaseConfigError = !url
  ? 'Missing VITE_SUPABASE_URL. Add the Supabase project URL to the Render environment variables.'
  : !key
    ? 'Missing VITE_SUPABASE_ANON_KEY. Add the Supabase publishable key to the Render environment variables.'
    : null

export const supabase = url && key ? createClient(url, key) : null
export const supabaseConfigured = Boolean(supabase)

if (supabaseConfigError) {
  console.warn(`[SAIS] ${supabaseConfigError}`)
}
