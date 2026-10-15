import { SplitText } from '../bits/SplitText'
import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'

type Props = {
  index?: string
  title: string
  hint: string
  className?: string
  children: ReactNode
}

export function Chapter({ index, title, hint, className, children }: Props) {
  const reduce = useReducedMotion()

  return (
    <motion.main
      className={className ? `chapter ${className}` : 'chapter'}
      initial={reduce ? false : { opacity: 0, y: 22 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
    >
      {index ? <p className="chapter-index">{index}</p> : null}
      <h1 className="chapter-title">
        <SplitText text={title} stagger={0.12} />
      </h1>
      <p className="chapter-hint">{hint}</p>
      {children}
    </motion.main>
  )
}
