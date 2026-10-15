import { useEffect, useState } from 'react'

type Props = {
  to: number
  duration?: number
}

export function CountUp({ to, duration = 2.1 }: Props) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    const start = performance.now()
    let frame = 0
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / (duration * 1000))
      const eased = 1 - (1 - t) ** 3
      setValue(Math.round(to * eased))
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [to, duration])

  return <>{value.toLocaleString('zh-CN')}</>
}
