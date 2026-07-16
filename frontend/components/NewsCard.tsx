import React from 'react';
import Image from 'next/image';
import { NewsArticle } from '../types';
import styles from './NewsCard.module.css';

interface NewsCardProps {
  article: NewsArticle;
  onGenerateAI: (id: string | number) => void;
  isGenerating: boolean;
}

function getTimeAgo(dateString: string): string {
  // Append 'Z' to treat the naive database timestamp as UTC
  const utcDateString = dateString.endsWith('Z') ? dateString : `${dateString}Z`;
  const date = new Date(utcDateString);
  const now = new Date();
  
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 0) return 'Just now'; // Handle slight future drift
  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  
  // Fallback to formatted date if more than 24 hours
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export default function NewsCard({ article, onGenerateAI, isGenerating }: NewsCardProps) {
  const displayTime = getTimeAgo(article.published_at);

  return (
    <div className={styles.card}>
      <div className={styles.imageContainer}>
        {article.image_url ? (
          <Image
            src={article.image_url}
            alt={article.title}
            className={styles.image}
            fill
            unoptimized
            onError={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              target.style.display = 'none';
              const ph = target.parentElement?.querySelector('[data-placeholder]') as HTMLElement;
              if (ph) ph.style.display = 'flex';
            }}
          />
        ) : null}
        {!article.image_url && (
          <Image
            src="/default-news.png"
            alt="Breaking News Placeholder"
            className={styles.image}
            fill
            unoptimized
          />
        )}
      </div>
      <div className={styles.content}>
        <div className={styles.header}>
          <span className={styles.source}>{article.source}</span>
          <div className={styles.timeRow}>
            <span className={styles.time}>{displayTime}</span>
            {article.credibility_score !== undefined && article.credibility_score !== null && article.credibility_status && (
              <span 
                className={styles.credibilityBadge} 
                style={{
                  background: article.credibility_score >= 90 ? '#dcfce7' : article.credibility_score >= 75 ? '#fef9c3' : '#fee2e2',
                  color: article.credibility_score >= 90 ? '#166534' : article.credibility_score >= 75 ? '#854d0e' : '#991b1b',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 600
                }}
                title={`Score: ${article.credibility_score}/100`}
              >
                {article.credibility_status}
              </span>
            )}
          </div>
        </div>
        
        <h3 className={styles.title}>{article.title}</h3>
        
        <div className={styles.location}>
          {article.state && article.state !== 'All' && article.state !== 'None' && article.state.trim() !== '' && (
            <span className={styles.tag}>{article.state}</span>
          )}
          {article.city && article.city !== 'All' && article.city !== 'None' && article.city.trim() !== '' && (
            <span className={styles.tag}>{article.city}</span>
          )}
        </div>
        
        <div className={styles.actions}>
          <a href={article.source_url} target="_blank" rel="noopener noreferrer" className={styles.linkButton}>
            Open Original
          </a>
          {article.references && (() => {
            try {
              const refs = JSON.parse(article.references);
              if (Array.isArray(refs) && refs.length > 0) {
                return (
                  <div className={styles.referencesDropdown}>
                    <button className={styles.referencesBtn}>
                      +{refs.length} Other Sources
                    </button>
                    <div className={styles.referencesList}>
                      {refs.map((ref, idx) => (
                        <a key={idx} href={ref} target="_blank" rel="noopener noreferrer">
                          Source {idx + 1}
                        </a>
                      ))}
                    </div>
                  </div>
                );
              }
            } catch {
              // Ignore parse error
            }
            return null;
          })()}
          <button 
            className={`${styles.aiButton} ${isGenerating ? styles.loading : ''}`}
            onClick={() => onGenerateAI(article.id)}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : article.status === 'processed' ? 'View AI Data' : 'Generate AI'}
          </button>
        </div>
      </div>
    </div>
  );
}
