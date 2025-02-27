"use client";

import { useEffect, useState } from "react";

export default function List() {
  const [documents, setDocuments] = useState<string[]>([]);
  const [dataFiles, setDataFiles] = useState<string[]>([]);

  // 파일 목록 가져오기
  const fetchFiles = async () => {
    try {
      const response = await fetch("http://localhost:7000/files");
      const data = await response.json();

      setDocuments(data.documents || []);  // ✅ 일반 문서
      setDataFiles(data.data_files || []); // ✅ CSV/JSON 파일
    } catch (error) {
      console.error("❌ 파일 목록을 불러오는 중 오류 발생:", error);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  return (
    <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl mx-auto">
      <h2 className="text-lg font-bold mb-3">📂 업로드된 파일 목록</h2>

      {/* ✅ 일반 문서 목록 */}
      <div className="mb-4">
        <h3 className="text-md font-semibold mb-2">📄 일반 문서</h3>
        {documents.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {documents.map((file, index) => (
              <div key={index} className="px-3 py-2 bg-gray-100 rounded-md shadow text-sm font-medium whitespace-nowrap">
                {file}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">📄 일반 문서가 없습니다.</p>
        )}
      </div>
      <br></br>
      {/* ✅ CSV/JSON 파일 목록 */}
      <div>
        <h3 className="text-md font-semibold mb-2">📊 데이터 파일</h3>
        {dataFiles.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {dataFiles.map((file, index) => (
              <div key={index} className="px-3 py-2 bg-blue-100 rounded-md shadow text-sm font-medium whitespace-nowrap">
                {file}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">📊 데이터 파일이 없습니다.</p>
        )}
      </div>
    </div>
  );
}
