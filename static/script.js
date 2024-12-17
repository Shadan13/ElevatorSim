function startSimulation() {
    const numPeople = document.getElementById("num_people").value;
    document.getElementById("status").innerText = "Simulation in progress...";
    document.getElementById("error").innerText = ""; // Clear error

    fetch("/init", {
        method: "POST",
        body: new URLSearchParams({ "num_people": numPeople })
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => { throw new Error(data.error); });
            }
            return response.json();
        })
        .then(() => update())
        .catch(err => {
            document.getElementById("error").innerText = err.message;
            document.getElementById("status").innerText = "Waiting for input...";
        });
}

function update() {
    fetch("/update")
        .then(response => response.json())
        .then(data => {
            document.getElementById("building").innerText = data.building_text;
            if (data.simulation_complete) {
                document.getElementById("status").innerText = "Simulation Complete!";
            } else {
                setTimeout(update, 500);
            }
        });
}