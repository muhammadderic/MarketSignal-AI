interface NewsBadgeProps {
  total: number;
}

export const NewsBadge = ({ total }: NewsBadgeProps) => (
  <span
    className="absolute top-1 right-1 inline-flex items-center justify-center
               min-w-[1.25rem] h-5 px-1 rounded-full
               bg-blue-600 text-white text-[10px] font-semibold leading-none"
    aria-label={`${total} news articles`}
  >
    {total}
  </span>
);