import { FACING_DEG, FACING_LABELS } from '../../lib/compass'

type Props = {
  /** 当前房间朝向（可选） */
  facing?: string
}

/** 固定上北下南的方位示意，无设备识别 */
export function Compass({ facing }: Props) {
  const faceLabel = facing && FACING_LABELS[facing] ? FACING_LABELS[facing] : null
  const faceDeg = facing && facing in FACING_DEG ? FACING_DEG[facing] : null

  return (
    <div className="compass" aria-label="方位：上北下南">
      <div className="compass-dial" aria-hidden>
        <div className="compass-ring">
          <span className="compass-mark n">北</span>
          <span className="compass-mark e">东</span>
          <span className="compass-mark s">南</span>
          <span className="compass-mark w">西</span>
          <i className="compass-needle" />
          {faceDeg != null ? (
            <i
              className="compass-facing"
              style={{
                transform: `translate(-50%, -100%) rotate(${faceDeg}deg)`,
              }}
              title={`朝向 ${faceLabel}`}
            />
          ) : null}
        </div>
      </div>
      <div className="compass-meta">
        <p className="dsh-kicker">方位</p>
        <p className="compass-readout">上北下南</p>
        <p className="compass-sub">平面图上方为北，下方为南。</p>
        {faceLabel ? <p className="compass-sub">此间朝向 · {faceLabel}</p> : null}
      </div>
    </div>
  )
}
