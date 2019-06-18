/*
* dataGerry - OpenSource Enterprise CMDB
* Copyright (C) 2019 NETHINKS GmbH
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as
* published by the Free Software Foundation, either version 3 of the
* License, or (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Affero General Public License for more details.

* You should have received a copy of the GNU Affero General Public License
* along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TypeViewComponent } from './components/type-view/type-view.component';
import { TypeListComponent } from './components/type-list/type-list.component';
import { TypeRoutingModule } from './type-routing.module';
import { LayoutModule } from '../../layout/layout.module';
import { DataTablesModule } from 'angular-datatables';
import { TypeAddComponent } from './components/type-add/type-add.component';
import { ArchwizardModule } from 'angular-archwizard';
import { TypeBuilderComponent } from './components/type-builder/type-builder.component';
import { TypeBasicStepComponent } from './components/type-builder/type-basic-step/type-basic-step.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TypeFieldsStepComponent } from './components/type-builder/type-fields-step/type-fields-step.component';
import { TypeHeaderComponent } from './components/type-header/type-header.component';
import { TypeQrComponent } from './components/type-qr/type-qr.component';
import { QRCodeModule } from 'angularx-qrcode';
import { TypeAccessStepComponent } from './components/type-builder/type-access-step/type-access-step.component';
import { NgSelectModule } from '@ng-select/ng-select';
import { TypeValidationStepComponent } from './components/type-builder/type-validation-step/type-validation-step.component';
import { RenderModule } from '../render/render.module';
import { BuilderModule } from './builder/builder.module';
import { TypeEditComponent } from './components/type-edit/type-edit.component';
import { TypeMetaStepComponent } from './components/type-builder/type-meta-step/type-meta-step.component';

@NgModule({
  declarations: [
    TypeViewComponent,
    TypeListComponent,
    TypeAddComponent,
    TypeBasicStepComponent,
    TypeFieldsStepComponent,
    TypeBuilderComponent,
    TypeHeaderComponent,
    TypeQrComponent,
    TypeAccessStepComponent,
    TypeValidationStepComponent,
    TypeEditComponent,
    TypeMetaStepComponent
  ],
  imports: [
    CommonModule,
    TypeRoutingModule,
    DataTablesModule,
    LayoutModule,
    ReactiveFormsModule,
    ArchwizardModule,
    QRCodeModule,
    NgSelectModule,
    RenderModule,
    BuilderModule,
    FormsModule
  ]
})
export class TypeModule {
}