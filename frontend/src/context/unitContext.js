import React, { createContext, useContext, useState } from "react";

const UnitContext = createContext();

export const useUnit = () => useContext(UnitContext);

export const UnitProvider = ({ children }) => {
    const [unit, setUnit] = useState("mm");
    const [nameColumn, setNameColumn] = useState('');

    return (
        <UnitContext.Provider value={{ unit, setUnit, nameColumn, setNameColumn }}>
            {children}
        </UnitContext.Provider>
    );
};
