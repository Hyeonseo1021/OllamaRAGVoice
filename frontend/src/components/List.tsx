"use client";

import { useEffect, useState } from "react";
import axios from "axios";

export default function List() {
    const [files, setFiles] = useState<string[]>([]);
  
    // 파일 목록 가져오기
    const fetchFiles = async () => {
      try {
        const response = await fetch("http://localhost:7000/files");
        const data = await response.json();
        setFiles(data.files || []);
      } catch (error) {
        console.error("❌ 파일 목록을 불러오는 중 오류 발생:", error);
      }
    };
  
    useEffect(() => {
      fetchFiles();
    }, []);
  
    return (
      <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl mx-auto">
        <h2 className="text-lg font-bold mb-3 flex items-center">
          📂 업로드된 파일 목록
        </h2>
        
        {files.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {files.map((file, index) => (
              <div key={index} className="px-3 py-2 bg-gray-100 rounded-md shadow text-sm font-medium whitespace-nowrap">
                {file}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">📂 업로드된 파일이 없습니다.</p>
        )}
      </div>
    );
  }