'use client';

import { useEffect, useRef } from 'react';
import { useIsFetching } from '@tanstack/react-query';

export default function TitleLoadingIndicator({ baseTitle = 'Chat Connect' }: { baseTitle?: string }) {
  const isFetching = useIsFetching();
  const originalTitleRef = useRef<string | null>(null);

  useEffect(() => {
    if (typeof document === 'undefined') return;
    if (originalTitleRef.current === null) {
      originalTitleRef.current = document.title || baseTitle;
    }

    if (isFetching > 0) {
      document.title = `⏳ Loading… | ${baseTitle}`;
    } else {
      document.title = originalTitleRef.current || baseTitle;
    }

    return () => {
      if (originalTitleRef.current !== null) {
        document.title = originalTitleRef.current;
      }
    };
  }, [isFetching, baseTitle]);

  return null;
}


