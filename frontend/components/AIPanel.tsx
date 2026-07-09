import React, { useState } from 'react';
import { AIResult } from '../types';
import styles from './AIPanel.module.css';
import Toast from './Toast';

interface AIPanelProps {
  result: AIResult | null;
  onClose: () => void;
}

export default function AIPanel({ result, onClose }: AIPanelProps) {
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  if (!result) return null;

  const handleCopy = (text: string | undefined, label: string) => {
    if (text) {
      navigator.clipboard.writeText(text);
      setToast({ message: `Copied ${label}`, type: 'success' });
    }
  };

  const handleCopyAll = () => {
    const allText = `
Category: ${result.category || 'N/A'}

Title: ${result.seo_title}
Slug: ${result.slug}
Description: ${result.meta_description}
Keywords: ${result.keywords}

Content:
${result.content}
    `.trim();
    navigator.clipboard.writeText(allText);
    setToast({ message: 'Copied all content', type: 'success' });
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.panel}>
        <div className={styles.header}>
          <h2>AI Generated SEO & Content</h2>
          <button className={styles.closeButton} onClick={onClose}>✕</button>
        </div>

        <div className={styles.content}>
          {result.category && (
            <div className={styles.fieldGroup}>
              <div className={styles.fieldHeader}>
                <label>Category</label>
                <button className={styles.copyBtn} onClick={() => handleCopy(result.category, 'Category')}>Copy</button>
              </div>
              <div className={styles.valueBox}>{result.category}</div>
            </div>
          )}

          <div className={styles.fieldGroup}>
            <div className={styles.fieldHeader}>
              <label>SEO Title</label>
              <button className={styles.copyBtn} onClick={() => handleCopy(result.seo_title, 'Title')}>Copy</button>
            </div>
            <div className={styles.valueBox}>{result.seo_title}</div>
          </div>

          <div className={styles.fieldGroup}>
            <div className={styles.fieldHeader}>
              <label>Slug</label>
              <button className={styles.copyBtn} onClick={() => handleCopy(result.slug, 'Slug')}>Copy</button>
            </div>
            <div className={styles.valueBox}>{result.slug}</div>
          </div>

          <div className={styles.fieldGroup}>
            <div className={styles.fieldHeader}>
              <label>Meta Description</label>
              <button className={styles.copyBtn} onClick={() => handleCopy(result.meta_description, 'Description')}>Copy</button>
            </div>
            <div className={styles.valueBox}>{result.meta_description}</div>
          </div>

          <div className={styles.fieldGroup}>
            <div className={styles.fieldHeader}>
              <label>Keywords</label>
              <button className={styles.copyBtn} onClick={() => handleCopy(result.keywords, 'Keywords')}>Copy</button>
            </div>
            <div className={styles.valueBox}>{result.keywords}</div>
          </div>

          <div className={styles.fieldGroup}>
            <div className={styles.fieldHeader}>
              <label>Content</label>
              <button className={styles.copyBtn} onClick={() => handleCopy(result.content, 'Content')}>Copy</button>
            </div>
            <div className={styles.valueBox}>{result.content}</div>
          </div>
        </div>

        <div className={styles.footer}>
          <button className={styles.copyAllBtn} onClick={handleCopyAll}>
            Copy All for Payload CMS
          </button>
        </div>
      </div>
      {toast && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast(null)} 
        />
      )}
    </div>
  );
}
