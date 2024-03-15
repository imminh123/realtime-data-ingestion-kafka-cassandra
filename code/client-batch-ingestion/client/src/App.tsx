import FileUpload from "./screen/FileUpload";

const tenants = [
  { id: 1, name: "Aalto University" },
  { id: 2, name: "Helsinki University" },
];

function App() {
  return (
    <>
      {tenants.map((item) => (
        <section key={item.id}>
          <h3>{item.name}</h3>
          <FileUpload tenant={item}/>
        </section>
      ))}
    </>
  );
}

export default App;
