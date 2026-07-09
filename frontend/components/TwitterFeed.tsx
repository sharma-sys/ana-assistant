'use client';
import { useEffect, useRef } from 'react';
import styles from './TwitterFeed.module.css';

interface TwitterFeedProps {
  twitterHandle?: string;
  height?: number;
}

export default function TwitterFeed({ twitterHandle = 'ANI', height = 1250 }: TwitterFeedProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;
    let script = document.getElementById("twitter-wjs") as HTMLScriptElement;

    const renderWidget = () => {
      // @ts-expect-error - Twitter widget types are not globally defined
      if (containerRef.current && window.twttr && window.twttr.widgets && isMounted) {
        containerRef.current.innerHTML = '';
        
        // @ts-expect-error - Twitter widget types are not globally defined
        window.twttr.widgets.createTimeline(
          {
            sourceType: 'profile',
            screenName: twitterHandle
          },
          containerRef.current,
          {
            height: height,
            theme: 'dark'
          }
        ).then((el: HTMLElement) => {
          console.log("Twitter widget loaded:", el);
          if (!el) {
            console.error("Twitter widget failed to load (likely due to browser privacy settings or adblocker).");
            if (containerRef.current) {
              containerRef.current.innerHTML = `
                <div style="padding: 20px; text-align: center; color: var(--text-muted); border: 1px dashed var(--border); border-radius: 8px; margin-top: 20px;">
                  <p style="margin-bottom: 10px;">Failed to load Twitter feed.</p>
                  <p style="font-size: 0.9em; margin-bottom: 15px;">Please check if your adblocker or tracking protection (e.g., Brave Shields) is blocking Twitter widgets.</p>
                  <a href="https://twitter.com/${twitterHandle}" target="_blank" rel="noopener noreferrer" style="color: var(--primary); text-decoration: underline;">
                    View @${twitterHandle} on X
                  </a>
                </div>
              `;
            }
          }
        }).catch((err: unknown) => {
          console.error("Error loading Twitter widget:", err);
        });
      }
    };

    if (!script) {
      script = document.createElement("script");
      script.id = "twitter-wjs";
      script.src = "https://platform.twitter.com/widgets.js";
      script.async = true;
      script.charset = "utf-8";
      document.body.appendChild(script);

      script.onload = renderWidget;
    } else {
      renderWidget();
    }
    
    return () => {
      isMounted = false;
    }
  }, [twitterHandle, height]);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Top Updates from X (Twitter)</h3>
      <div className={styles.feedWrapper} ref={containerRef}>
        {/* Widget will be dynamically injected here */}
      </div>
    </div>
  );
}
