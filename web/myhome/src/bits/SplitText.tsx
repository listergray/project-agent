import { motion, useReducedMotion } from 'motion/react'

type Props = {
  text: string
  className?: string
  delay?: number
  stagger?: number
}

export function SplitText({ text, className, delay = 0, stagger = 0.1 }: Props) {
  const reduce = useReducedMotion()

  return (
    <span className={className} aria-label={text}>
      {Array.from(text).map((ch, i) => (
        <motion.span
          key={`${ch}-${i}`}
          className="split-ch"
          aria-hidden
          initial={reduce ? false : { opacity: 0, y: 18, filter: 'blur(10px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{
            delay: delay + i * stagger,
            duration: 0.75,
            ease: [0.16, 1, 0.3, 1],
          }}
        >
          {ch}
        </motion.span>
      ))}
    </span>
  )
}
