import type { FormEvent, ReactNode } from 'react'

type FieldProps = {
  label: string
  children: ReactNode
  className?: string
}

export function Field({ label, children, className }: FieldProps) {
  return (
    <label className={className ? `field ${className}` : 'field'}>
      <span>{label}</span>
      {children}
    </label>
  )
}

export function readForm(e: FormEvent<HTMLFormElement>) {
  return new FormData(e.currentTarget)
}
