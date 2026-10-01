import { Link, type LinkProps } from 'react-router-dom'
import { prefetchPageForPath } from '../../routes/pageLoaders'

type PrefetchLinkProps = Omit<LinkProps, 'to'> & { to: string }

// A Link that starts downloading its destination page as soon as the pointer
// reaches it (hover, or the first touch) or it gains keyboard focus — before the click.
export default function PrefetchLink({ to, ...props }: PrefetchLinkProps) {
  const prefetch = () => prefetchPageForPath(to)
  return <Link to={to} onPointerEnter={prefetch} onFocus={prefetch} {...props} />
}
