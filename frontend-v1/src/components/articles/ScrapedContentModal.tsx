import { useEffect, useMemo, useRef, useState } from 'react';
import { Copy, X } from 'lucide-react';
import { useArticle } from '@/hooks/useArticle';
import { useUpdateArticleContent } from '@/hooks/useUpdateArticleContent';
import type { ArticleDetail } from '@/types/article';

export interface ScrapedContentModalProps {
  articleId: number | null;
  onClose: () => void;
}

/**
 * Modal for reviewing, editing, and saving an article's `scraped_content`.
 * Implements FEAT-007 FR-015 / BR-013 / NFR-003 and D1–D8 from the task plan.
 */
export function ScrapedContentModal({
  articleId,
  onClose,
}: ScrapedContentModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const open = articleId !== null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  // Close when the native dialog requests it (Esc key, backdrop optional).
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const handleClose = () => onClose();
    dialog.addEventListener('close', handleClose);
    return () => dialog.removeEventListener('close', handleClose);
  }, [onClose]);

  return (
    <dialog
      ref={dialogRef}
      className="w-full max-w-3xl rounded-lg border border-slate-200 bg-white p-0 shadow-xl backdrop:bg-slate-900/50"
      aria-labelledby="scraped-content-title"
    >
      {open ? (
        <ScrapedContentEditor articleId={articleId} onClose={onClose} />
      ) : null}
    </dialog>
  );
}

interface ScrapedContentEditorProps {
  articleId: number;
  onClose: () => void;
}

function ScrapedContentEditor({
  articleId,
  onClose,
}: ScrapedContentEditorProps) {
  const { data, isLoading, isError, error, refetch } = useArticle(articleId);
  const mutation = useUpdateArticleContent();

  if (isLoading) {
    return (
      <div className="space-y-4 p-6" role="status" aria-label="Loading content">
        <div className="h-5 w-2/3 animate-pulse rounded bg-slate-200" />
        <div className="h-40 w-full animate-pulse rounded bg-slate-100" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="space-y-3 p-6">
        <h2
          id="scraped-content-title"
          className="text-lg font-semibold text-slate-900"
        >
          Review / Edit Content
        </h2>
        <p className="text-sm text-red-700" role="alert">
          Failed to load article: {error?.message ?? 'unknown error'}
        </p>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Close
          </button>
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded-md border border-slate-900 bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <ScrapedContentForm
      key={articleId}
      article={data}
      onClose={onClose}
      isSaving={mutation.isPending}
      saveError={mutation.error?.message ?? null}
      onSave={(content) =>
        mutation.mutate(
          { articleId, scrapedContent: content },
          { onSuccess: () => onClose() },
        )
      }
    />
  );
}

interface ScrapedContentFormProps {
  article: ArticleDetail;
  onClose: () => void;
  isSaving: boolean;
  saveError: string | null;
  onSave: (content: string) => void;
}

type CopyState = 'idle' | 'copied' | 'error';

function ScrapedContentForm({
  article,
  onClose,
  isSaving,
  saveError,
  onSave,
}: ScrapedContentFormProps) {
  const [content, setContent] = useState<string>(article.scraped_content ?? '');
  const [copyState, setCopyState] = useState<CopyState>('idle');
  const copyResetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (copyResetTimer.current) {
        clearTimeout(copyResetTimer.current);
      }
    };
  }, []);

  const { characterCount, wordCount } = useMemo(() => {
    const characters = content.length;
    const words = content.trim() === '' ? 0 : content.trim().split(/\s+/).length;
    return { characterCount: characters, wordCount: words };
  }, [content]);

  const isBlank = content.trim() === '';
  const hasSavedContent = (article.scraped_content ?? '') !== '';
  const saveDisabled = isBlank || isSaving;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
    if (copyResetTimer.current) clearTimeout(copyResetTimer.current);
    copyResetTimer.current = setTimeout(() => setCopyState('idle'), 2000);
  };

  const copyLabel =
    copyState === 'copied'
      ? 'Copied!'
      : copyState === 'error'
        ? 'Copy failed'
        : 'Copy to Clipboard';

  return (
    <div className="flex flex-col">
      <header className="flex items-start justify-between gap-3 border-b border-slate-200 p-4">
        <div className="min-w-0">
          <h2
            id="scraped-content-title"
            className="truncate text-lg font-semibold text-slate-900"
          >
            Review / Edit Content
          </h2>
          <p className="truncate text-sm text-slate-600">{article.title}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close editor"
          className="shrink-0 rounded p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </header>

      <div className="space-y-2 p-4">
        {!hasSavedContent ? (
          <p className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-800">
            No saved content yet — paste or type content to enable saving.
          </p>
        ) : null}
        <label htmlFor="scraped-content-textarea" className="sr-only">
          Scraped article content
        </label>
        <textarea
          id="scraped-content-textarea"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          spellCheck={false}
          className="h-72 w-full resize-y rounded-md border border-slate-300 bg-slate-50 p-3 font-mono text-sm text-slate-900 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400"
          placeholder="Paste or type the cleaned article body here…"
        />
        {saveError ? (
          <p className="text-sm text-red-700" role="alert">
            Save failed: {saveError}
          </p>
        ) : null}
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 p-4">
        <div className="flex items-center gap-4 text-xs text-slate-600">
          <span data-testid="character-count">{characterCount} characters</span>
          <span data-testid="word-count">{wordCount} words</span>
          <button
            type="button"
            onClick={() => void handleCopy()}
            disabled={content.length === 0}
            className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            {copyLabel}
          </button>
          {copyState !== 'idle' ? (
            <span role="status" className="text-xs text-slate-500">
              {copyState === 'copied' ? 'Copied to clipboard.' : 'Copy failed.'}
            </span>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onSave(content)}
            disabled={saveDisabled}
            title={isBlank ? 'Content is empty' : undefined}
            className="rounded-md border border-slate-900 bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSaving ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </footer>
    </div>
  );
}