import React from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  height?: string;
  readOnly?: boolean;
  fileName?: string;
}

// 根据文件名自动检测语言
const detectLanguage = (fileName?: string): string => {
  if (!fileName) return 'python';
  
  const ext = fileName.toLowerCase().split('.').pop();
  const languageMap: { [key: string]: string } = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'jsx': 'javascript',
    'tsx': 'typescript',
    'json': 'json',
    'html': 'html',
    'css': 'css',
    'sh': 'shell',
    'bash': 'shell',
    'yml': 'yaml',
    'yaml': 'yaml',
    'xml': 'xml',
    'sql': 'sql',
    'md': 'markdown',
    'txt': 'plaintext',
  };
  
  return languageMap[ext || ''] || 'plaintext';
};

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language,
  height = '500px',
  readOnly = false,
  fileName
}) => {
  const editorLanguage = language || detectLanguage(fileName);
  const handleEditorChange = (value: string | undefined) => {
    onChange(value || '');
  };

  return (
    <Editor
      height={height}
      defaultLanguage={editorLanguage}
      language={editorLanguage}
      value={value}
      onChange={handleEditorChange}
      theme="vs-dark"
      options={{
        readOnly,
        minimap: { enabled: true },
        fontSize: 14,
        lineNumbers: 'on',
        roundedSelection: false,
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        wordWrap: 'on',
        folding: true,
        lineDecorationsWidth: 10,
        lineNumbersMinChars: 4,
        renderLineHighlight: 'all',
        scrollbar: {
          vertical: 'visible',
          horizontal: 'visible',
          verticalScrollbarSize: 10,
          horizontalScrollbarSize: 10
        },
        suggestOnTriggerCharacters: true,
        quickSuggestions: true,
        formatOnPaste: true,
        formatOnType: true,
      }}
    />
  );
};

export default CodeEditor;
