from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json
import uvicorn
app = FastAPI()

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="The ID of the patient", example="P001")]
    name: Annotated[str, Field(..., description="The name of the patient", example="John Doe")]
    city: Annotated[str, Field(..., description="The city of the patient", example="New York")]
    age:  Annotated[int, Field(..., gt = 0, lt = 100, description="The age of the patient", example=30)]
    gender: Annotated[Literal['male', 'female'], Field(..., description="The gender of the patient", example="Male")]
    height: Annotated[float, Field( ..., gt = 0, lt = 2.5, description="The height of the patient in cm", example=1.75)]
    weight: Annotated[float, Field(...,gt = 0, description="The weight of the patient in kg", example=70.0)]
    
    @computed_field
    @property
    def bmi(self) -> float:
        return self.weight / (self.height ** 2)

    # computed field will call the computed field again
    # so first verdict triggered using using self.bmi than bmi triggered  
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi >= 18.5 and self.bmi < 25:
            return "Normal"
        elif self.bmi >= 25 and self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"

def load_data():
    with open("pateints.json", "r") as f:
        data = json.load(f) 
    return data

def save_data(data):
    with open("pateints.json", "w") as f:
        json.dump(data, f)
# save the data to the file
@app.get("/")
def hello(): # decorator function
    return {"message": "pateint management system"}


@app.get("/about")
def about():
    
    return {"message": "A full stack pateint records"}

@app.get('/view')
def view():
    data = load_data()
    return data

@app.get('/pateint/{pateint_id}')
def view_pateint(pateint_id: str = Path(..., description="The ID of the pateint to view", example="P001")):
    # three dots meaning is reqired
    data = load_data()

    if pateint_id not in data:
        raise HTTPException(status_code=404, detail="Pateint not found")
    else:
        return data[pateint_id]
@app.get('/sort')
def sort(sort_by: str = Query(..., description="sort on the basis of height, weight,  or bmi", example="170cm"),
    order: str = Query('asc',)):

    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field select from {valid_fields}")
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order")

    data = load_data()
    sort_order = -1 if order == 'desc' else 1
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=sort_order)
    return data

@app.post('/create')
def create_pateint(pateint: Patient):# pydantic will check here for dta validation
    # as pateint is here is pydantic object
    # and data is in dictionary format
    # we will combine both for the validation
    #load the existing data
    data = load_data()
    # check if the pateint already exists
    if pateint.id in data:
        raise HTTPException(status_code=400, detail="Pateint already exists")
 
 # new pateint data will be added to the data
 # using checking the pydantic object to use validation
 # it applied all the checks and then add the data to the data
    data[pateint.id] = pateint.model_dump()
    

# now we have to save the data
    save_data(data)
    return JSONResponse(content={"message": "Pateint created successfully"}, status_code=201)




class PateintUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None, description="The name of the patient", example="John Doe")]
    city: Annotated[Optional[str], Field(default=None, description="The city of the patient", example="New York")]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=100, description="The age of the patient", example=30)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None, description="The gender of the patient", example="male")]
    height: Annotated[Optional[float], Field(default=None, gt=0, lt=2.5, description="The height of the patient in cm", example=1.75)]
    weight: Annotated[Optional[float], Field(default=None, gt=0, description="The weight of the patient in kg", example=70.0)]

@app.put('/edit/{pateint_id}')
def update_pateint(pateint_id: str, pateint_update: PateintUpdate):
    data = load_data()
    if pateint_id not in data:
        raise HTTPException(status_code=404, detail="Pateint not found")
    existing_pateint_info = data[pateint_id].copy()
        
    updated_pateint_info = pateint_update.model_dump(exclude_unset=True)

    for key, value in updated_pateint_info.items():
        if value is not None:
            existing_pateint_info[key] = value
    
    # Normalize gender to lowercase to match Patient model expectations
    if 'gender' in existing_pateint_info:
        gender = existing_pateint_info['gender']
        if isinstance(gender, str):
            existing_pateint_info['gender'] = gender.lower()
    
    # existing_pateint_info -> pydantic object -> updated bmi + verdict -> pydantic object -> dict
    existing_pateint_info['id'] = pateint_id
    pateint_pydantic_object = Patient(**existing_pateint_info)
    existing_pateint_info = pateint_pydantic_object.model_dump(exclude='id')
    data[pateint_id] = existing_pateint_info
    save_data(data)
    return JSONResponse(content={"message": "Pateint updated successfully"}, status_code=200)

@app.delete('/delete/{pateint_id}')
def delete_pateint(pateint_id: str):
    data = load_data()
    if pateint_id not in data:
        raise HTTPException(status_code=404, detail="Pateint not found")
    else:
        del data[pateint_id]
        save_data(data)
        return JSONResponse(content={"message": "Pateint deleted successfully"}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


