import React from 'react';
import Image from 'next/image';
import { NewsArticle } from '../types';
import styles from './CompactNewsCard.module.css';

interface CompactNewsCardProps {
  article: NewsArticle;
}

export default function CompactNewsCard({ article }: CompactNewsCardProps) {
  const publishedDate = new Date(article.published_at + 'Z');
  
  // Calculate relative time (e.g., "4 hours ago")
  const getRelativeTime = (date: Date) => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} days ago`;
  };

  const relativeTime = getRelativeTime(publishedDate);

  return (
    <a href={article.source_url} target="_blank" rel="noopener noreferrer" className={styles.card}>
      <div className={styles.content}>
        <div className={styles.header}>
          <span className={styles.source}>{article.source}</span>
          <span className={styles.time}>{relativeTime}</span>
        </div>
        <h3 className={styles.title} title={article.title}>
          {article.title}
        </h3>
      </div>
      <div className={styles.imageContainer}>
        <Image 
          src={article.image_url || '/default-news.png'} 
          alt={article.title} 
          className={styles.image}
          fill
          unoptimized
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/default-news.png';
            target.srcset = '';
          }}
        />
      </div>
    </a>
  );
}
