export function PageHeader({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-8 animate-fade-in">
      <h1 className="text-2xl font-semibold tracking-tight text-white">
        {title}
      </h1>
      {description ? (
        <p className="mt-2 max-w-2xl text-sm text-ink-muted">{description}</p>
      ) : null}
    </div>
  );
}
