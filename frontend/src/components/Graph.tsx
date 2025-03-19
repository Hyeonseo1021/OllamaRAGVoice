"use client";

export default function Graph({ imageBase64 }: { imageBase64: string }) {
  return (
    <div className="mt-4">
      {imageBase64 ? (
        <img
          src={`data:image/png;base64,${imageBase64}`}
          alt="Generated Graph"
          className="border rounded-lg shadow-md"
        />
      ) : (
        <p>📊 그래프가 없습니다.</p>
      )}
    </div>
  );
}
