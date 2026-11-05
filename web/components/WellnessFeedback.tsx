'use client'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { todayISO } from '@/lib/utils'

export default function WellnessFeedback() {
  const userId = useAuthStore(s => s.userId)
  const date = todayISO()
  const qc = useQueryClient()
  const [score, setScore] = useState('3')
  const [notes, setNotes] = useState('')
  const { data } = useQuery({ queryKey: ['feedback', userId, date], enabled: !!userId,
    queryFn: async () => {
      try { return (await api.get(`/wellness-feedback/${userId}?date=${date}`)).data }
      catch (error: any) { if (error.response?.status === 404) return null; throw error }
    }, retry: false })
  const save = useMutation({ mutationFn: async () => {
    return (await api.post('/wellness-feedback', { user_id: userId, date, feeling_score: Number(score), notes: notes || null })).data
  }, onSuccess: () => qc.invalidateQueries({ queryKey: ['feedback', userId, date] }) })
  return <section className="bg-surface rounded-2xl p-5 space-y-3" aria-label="Feedback diário">
    <h2 className="font-bold text-text">Como você se sente hoje?</h2>
    {data ? <p role="status" className="text-sub">Feedback registrado: {data.feeling_score}/5</p> : <form className="flex flex-wrap gap-3" onSubmit={e => { e.preventDefault(); save.mutate() }}>
      <label className="text-sub">Bem-estar (1–5) <select aria-label="Bem-estar" value={score} onChange={e => setScore(e.target.value)} className="bg-bg text-text rounded p-2">
        {[1, 2, 3, 4, 5].map(value => <option key={value} value={value}>{value}</option>)}
      </select></label>
      <input aria-label="Anotação do feedback" placeholder="Anotação opcional" value={notes} onChange={e => setNotes(e.target.value)} className="bg-bg text-text rounded p-2" />
      <button disabled={save.isPending} className="bg-brand text-white rounded px-4 py-2">Salvar feedback</button>
      {save.isError && <p role="alert">Não foi possível salvar. Tente novamente.</p>}
    </form>}
  </section>
}
