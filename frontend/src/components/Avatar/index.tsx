interface AvatarProps {
  name: string;
  imageUrl: string | null;
  // Pixel size; also sets the image's width/height so the layout doesn't jump.
  size?: number;
}

// A person's photo, or the first letter of their name when they have none.
// Decorative next to a visible name (alt=""), so screen readers don't read it twice.
export default function Avatar({ name, imageUrl, size = 32 }: AvatarProps) {
  const style = { width: size, height: size };

  return imageUrl ? (
    <img
      src={imageUrl}
      alt=""
      width={size}
      height={size}
      decoding="async"
      style={style}
      className="shrink-0 rounded-full object-cover"
    />
  ) : (
    <span
      aria-hidden="true"
      style={style}
      className="flex shrink-0 items-center justify-center rounded-full bg-sees-teal text-sm font-medium text-sees-mint"
    >
      {name.charAt(0).toUpperCase()}
    </span>
  );
}
