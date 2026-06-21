const STACK = [
  'QNX RTOS',
  'Claude API',
  'Arize',
  'Supabase',
  'OpenCV DNN',
  'YOLOv8n · ONNX',
  'Poke',
  'UC IPM',
  'Raspberry Pi 5',
]

export function Trust() {
  const row = [...STACK, ...STACK]
  return (
    <section className="border-b border-line bg-paper py-7">
      <div className="mx-auto mb-5 max-w-6xl px-5 md:px-8">
        <p className="text-center font-mono text-[11px] uppercase tracking-[0.22em] text-muted">
          A hardware-honest stack — built for the field
        </p>
      </div>
      <div className="relative overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_12%,black_88%,transparent)]">
        <div className="flex w-max animate-marquee items-center gap-12 pr-12">
          {row.map((name, i) => (
            <span
              key={i}
              className="flex shrink-0 items-center gap-3 font-display text-xl font-medium text-forest/55"
            >
              <span className="inline-block size-1.5 rotate-45 bg-gold/70" />
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
