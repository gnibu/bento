export function Message({ it, s }: { it: Item; s: Stats | null }) {
  if (it.kind === 'user') {
    return root(
      <div className="user">
        {it.text}
      </div>)
  }
  if (it.kind === 'approval') {
    return (
      <div className="approval" />
    )
  }
  if (it.kind === 'turn') {
    return (
      <div className="turn">
        {s ? (
          <span className="changes">
            {`${s.files} file${s.files > 1 ? 's' : ''} changed `}<span className="ad">{'+' + s.add}</span>{' '}<span className="rm">{'-' + s.del}</span>{' '}
          </span>
        ) : null}
      </div>
    )
  }
  return null
}
