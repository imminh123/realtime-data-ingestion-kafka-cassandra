import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";

function shallowCompareArray(arr1: any[], arr2: any[]) {
  return arr1.length === arr2.length && arr1.every((value, index) => value === arr2[index])
}  
const FileUpload = ({ tenant }: { tenant: { id: number; name: string } }) => {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    getFiles();
  }, []);

  const getFiles = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/tenant/${tenant.id}`,
        {
          method: "GET",
        }
      );

      if (response.ok) {
        const data = await response.json();
        if(!shallowCompareArray(files, data))
          setFiles(data);
      } else {
        console.error(
          "Failed to upload file. Server returned:",
          response.statusText
        );
      }
    } catch (error) {
      console.error("An error occurred while uploading the file:", error);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]; // Assuming only one file is dropped
    const formData = new FormData();

    formData.append("file", file);

    try {
      const response = await fetch(
        `http://localhost:8000/upload-file/${tenant.id}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (response.ok) {
        getFiles()
      } else {
        console.error(
          "Failed to upload file. Server returned:",
          response.statusText
        );
      }
    } catch (error) {
      console.error("An error occurred while uploading the file:", error);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div {...getRootProps()} style={dropzoneStyle}>
      <ul style={{ display: "block" }}>
        {files.map((item) => (
          <li>{item}</li>
        ))}
      </ul>
      <input {...getInputProps()} />

      {isDragActive ? (
        <p>Drop the files here ...</p>
      ) : (
        <p>Drag 'n' drop some files here, or click to select files</p>
      )}
    </div>
  );
};

const dropzoneStyle = {
  padding: "10px",
  width: "100%",
  minHeight: "200px",
  alignItems: "center",
  justifyContent: "center",
  border: "2px dashed #eeeeee",
  borderRadius: "4px",
  cursor: "pointer",
};

export default FileUpload;
