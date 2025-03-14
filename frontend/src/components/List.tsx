"use client";

import { useEffect, useState } from "react";
import styles from "../styles/list.module.css"; // ✅ 새로운 CSS 파일 불러오기

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

  // 파일 삭제 요청 함수
  const deleteFile = async (filename: string, isDataFile: boolean) => {
    try {
      const url = isDataFile
        ? `http://localhost:7000/delete/file?filename=${filename}`
        : `http://localhost:7000/delete/document?filename=${filename}`;

      const response = await fetch(url, { method: "DELETE" });
      const result = await response.json();
      
      if (response.ok) {
        console.log("✅ 삭제 완료:", result.message);
        fetchFiles(); // 삭제 후 목록 새로고침
      } else {
        console.error("❌ 삭제 실패:", result.detail);
      }
    } catch (error) {
      console.error("❌ 삭제 중 오류 발생:", error);
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
              <div key={index} className="flex items-center px-3 py-2 bg-gray-100 rounded-md shadow text-sm font-medium whitespace-nowrap">
                {file}
                <button
                  onClick={() => deleteFile(file, false)}
                  className="ml-2 bg-red-500 text-white px-2 py-1 rounded-md text-xs hover:bg-red-700"
                >
                  삭제
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">📄 일반 문서가 없습니다.</p>
        )}
      </div>
      
      {/* ✅ CSV/JSON 파일 목록 */}
      <div>
        <h3 className="text-md font-semibold mb-2">📊 데이터 파일</h3>
        {dataFiles.length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {dataFiles.map((file, index) => (
              <div key={index} className="flex items-center px-3 py-2 bg-blue-100 rounded-md shadow text-sm font-medium whitespace-nowrap">
                {file}
                <button
                  onClick={() => deleteFile(file, true)}
                  className="ml-2 bg-red-500 text-white px-2 py-1 rounded-md text-xs hover:bg-red-700"
                >
                  삭제
                </button>
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